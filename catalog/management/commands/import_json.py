import json
import time
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (
    Product, Brand, Category,
    ProductImage, ProductProperty, ProductCertificate,
)

SLUG_FIXES = {
    # 22 товара
    'zaryadnye-ustroistva': 'zaryadnye-ustroystva',
    # 20 товаров
    'akkumulyatory-dlya-elektroinstrumenta-i-tehniki': 'akkumulyatory-dlya-elektroinstrumenta-i-tekhniki',
    # 7 товаров
    'lestnitsy-alyuminievye-tryokhsektsionnye': 'lestnitsy-alyuminievye-trekhsektsionnye',
    # 4 товара
    'lestnitsy-transformer': 'lestnitsy-transformery',
    # 2 товара
    'patrony-dlya-dreli-shurupoverta': 'patrony-dlya-dreli',
}


class Command(BaseCommand):
    help = 'Импорт товаров из JSON сайта utake'

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str)
        parser.add_argument(
            '--limit', type=int, default=0,
            help='Ограничить количество товаров (0 = все)',
        )
        parser.add_argument(
            '--skip-features', action='store_true',
            help='Не импортировать характеристики',
        )
        parser.add_argument(
            '--skip-documents', action='store_true',
            help='Не импортировать документы',
        )
        parser.add_argument(
            '--skip-images', action='store_true',
            help='Не импортировать галерею изображений',
        )

    def handle(self, *args, **options):
        path = options['json_path']
        limit = options['limit']
        skip_features = options['skip_features']
        skip_documents = options['skip_documents']
        skip_images = options['skip_images']

        self.stdout.write(f'Читаю {path}...')
        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'items' in data:
            data = data['items']

        if limit:
            data = data[:limit]

        self.stdout.write(f'Товаров к импорту: {len(data)}')

        # Кэш категорий и брендов для скорости
        categories_by_slug = {c.slug: c for c in Category.objects.all()}
        brands_by_name = {b.name: b for b in Brand.objects.all()}

        self.stdout.write(f'Категорий в БД: {len(categories_by_slug)}')
        self.stdout.write(f'Брендов в БД: {len(brands_by_name)}')
        self.stdout.write('')

        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'no_category': 0,
            'no_brand': 0,
        }

        t0 = time.time()

        for i, item in enumerate(data, 1):
            try:
                with transaction.atomic():
                    result = self._import_one(
                        item,
                        categories_by_slug,
                        brands_by_name,
                        skip_features=skip_features,
                        skip_documents=skip_documents,
                        skip_images=skip_images,
                    )
                    stats[result] += 1
                    if result in ('created', 'updated'):
                        if not item.get('_category_found'):
                            stats['no_category'] += 1
            except Exception as e:
                stats['errors'] += 1
                self.stderr.write(
                    f'  [{i}] ОШИБКА sku={item.get("sku")}: {e}'
                )

            if i % 100 == 0:
                elapsed = time.time() - t0
                self.stdout.write(
                    f'  {i}/{len(data)} — '
                    f'создано {stats["created"]}, '
                    f'обновлено {stats["updated"]}, '
                    f'ошибок {stats["errors"]}, '
                    f'{elapsed:.1f}с'
                )

        elapsed = time.time() - t0
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Готово за {elapsed:.1f}с\n'
            f'  Создано:              {stats["created"]}\n'
            f'  Обновлено:            {stats["updated"]}\n'
            f'  Пропущено:            {stats["skipped"]}\n'
            f'  Без категории:        {stats["no_category"]}\n'
            f'  Ошибок:               {stats["errors"]}'
        ))

    def _import_one(self, item, categories_by_slug, brands_by_name,
                    skip_features, skip_documents, skip_images):
        sku = item.get('sku')
        if not sku:
            return 'skipped'

        # --- категория ---
        category = self._resolve_category(item, categories_by_slug)
        item['_category_found'] = category is not None

        # --- бренд ---
        brand = self._resolve_brand(item, brands_by_name)

        # --- сертификация ---
        docs_note = item.get('documents_note') or ''
        no_cert = 'не подлежит' in docs_note.lower()

        # --- цена ---
        price = self._to_decimal(item.get('price')) or Decimal('0')

        # --- основное изображение ---
        main_image_url = item.get('image') or ''

        defaults = {
            'external_id': str(item.get('id', '')),
            'name': (item.get('name') or '')[:500],
            'price': price,
            'brand': brand,
            'category': category,
            'description': item.get('description') or '',
            'no_certificate_required': no_cert,
            'image_url': main_image_url,
        }

        product, created = Product.objects.update_or_create(
            article=sku,
            defaults=defaults,
        )

        # --- галерея изображений ---
        if not skip_images:
            self._import_images(product, item.get('images') or [])

        # --- характеристики ---
        if not skip_features:
            self._import_features(product, item.get('features') or [])

        # --- документы ---
        if not skip_documents:
            self._import_documents(product, item.get('documents') or [])

        return 'created' if created else 'updated'

    # def _resolve_category(self, item, categories_by_slug):
    #     cats = item.get('categories') or []
    #     if not cats:
    #         return None
    #     url = cats[-1].rstrip('/')
    #     slug = url.rsplit('/', 1)[-1]
    #     return categories_by_slug.get(slug)
    # def _resolve_category(self, item, categories_by_slug):
    #     cats = item.get('categories') or []
    #     if not cats:
    #         return None
    #     # идём с конца к началу, берём первый известный slug
    #     for url in reversed(cats):
    #         slug = url.rstrip('/').rsplit('/', 1)[-1].strip()
    #         if slug in categories_by_slug:
    #             return categories_by_slug[slug]
    #     return None

    def _resolve_category(self, item, categories_by_slug):
        cats = item.get('categories') or []
        if not cats:
            return None
        for url in reversed(cats):
            slug = url.rstrip('/').rsplit('/', 1)[-1].strip()
            # сначала пробуем как есть
            if slug in categories_by_slug:
                return categories_by_slug[slug]
            # потом пробуем через фикс
            fixed = SLUG_FIXES.get(slug)
            if fixed and fixed in categories_by_slug:
                return categories_by_slug[fixed]
        return None

    def _resolve_brand(self, item, brands_by_name):
        name = (item.get('brand') or '').strip()
        if not name:
            return None
        if name in brands_by_name:
            return brands_by_name[name]

        base_slug = slugify(name) or 'brand'
        slug = base_slug
        counter = 1
        while Brand.objects.filter(slug=slug).exists():
            counter += 1
            slug = f'{base_slug}-{counter}'

        brand = Brand.objects.create(name=name, slug=slug)
        brands_by_name[name] = brand
        return brand

    def _import_images(self, product, images):
        """Удаляет старые и создаёт новые ProductImage."""
        if not images:
            return
        ProductImage.objects.filter(product=product).delete()
        objs = []
        for i, url in enumerate(images):
            if not url:
                continue
            objs.append(ProductImage(
                product=product,
                image_url=url[:1000],
                is_main=(i == 0),
                order=i,
            ))
        if objs:
            ProductImage.objects.bulk_create(objs)

    def _import_features(self, product, features):
        """Удаляет старые и создаёт новые ProductProperty."""
        if not features:
            return
        ProductProperty.objects.filter(product=product).delete()
        objs = []
        seen = set()
        for f in features:
            name = (f.get('name') or '').strip()[:255]
            value = (f.get('value') or '').strip()[:500]
            if not name or not value or name in seen:
                continue
            seen.add(name)
            objs.append(ProductProperty(
                product=product, name=name, value=value,
            ))
        if objs:
            ProductProperty.objects.bulk_create(objs)

    def _import_documents(self, product, documents):
        """Удаляет старые и создаёт новые ProductCertificate."""
        if not documents:
            return
        ProductCertificate.objects.filter(product=product).delete()
        objs = []
        for i, d in enumerate(documents):
            title = (d.get('title') or '').strip()[:255]
            url = (d.get('url') or '').strip()[:500]
            if not title:
                continue
            objs.append(ProductCertificate(
                product=product,
                name=title,
                url=url,
                sort_order=i,
            ))
        if objs:
            ProductCertificate.objects.bulk_create(objs)

    @staticmethod
    def _to_decimal(value):
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None