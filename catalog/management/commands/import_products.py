# catalog/management/commands/import_products.py
import json
import re
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Category, Product, ProductProperty, ProductImage


class Command(BaseCommand):
    help = 'Импорт товаров из двух JSON файлов'

    def add_arguments(self, parser):
        parser.add_argument('category_file', type=str, help='Путь к файлу с категориями и товарами')
        parser.add_argument('details_file', type=str, help='Путь к файлу с деталями товаров')

    def extract_id_from_url(self, url):
        """Извлекает ID товара из URL"""
        match = re.search(r'/(\d+)/$', url)
        return match.group(1) if match else None

    def handle(self, *args, **options):
        category_file = options['category_file']
        details_file = options['details_file']

        # Проверяем существование файлов
        self.stdout.write(f'Текущая директория: {os.getcwd()}')

        if not os.path.exists(category_file):
            self.stdout.write(self.style.ERROR(f'❌ Файл не найден: {category_file}'))
            return

        if not os.path.exists(details_file):
            self.stdout.write(self.style.ERROR(f'❌ Файл не найден: {details_file}'))
            return

        self.stdout.write(f'✅ Файл найден: {category_file}')

        # Загружаем данные
        try:
            with open(category_file, 'r', encoding='utf-8') as f:
                category_data = json.load(f)
            self.stdout.write(f'✅ Загружено {len(category_data)} записей')
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка парсинга JSON: {e}'))
            return

        try:
            with open(details_file, 'r', encoding='utf-8') as f:
                details_data = json.load(f)
            self.stdout.write(f'✅ Загружено {len(details_data)} записей с деталями')
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка парсинга JSON: {e}'))
            return

        # Создаем словарь деталей по URL
        details_dict = {}
        for detail in details_data:
            url = detail.get('url')
            if url:
                details_dict[url] = detail

        # Создаем категорию
        category, created = Category.objects.get_or_create(
            name='Аккумуляторные шуруповерты и дрели',
            defaults={'slug': 'akkumulyatornye-shurupoverty-i-dreli'}
        )

        # Словарь для дедупликации
        seen_products = {}
        success_count = 0
        skip_count = 0
        update_count = 0

        for item in category_data:
            # Пропускаем записи без ID
            if item.get('id') is None:
                skip_count += 1
                continue

            product_id = str(item['id'])

            # Пропускаем дубликаты
            if product_id in seen_products:
                skip_count += 1
                continue
            seen_products[product_id] = True

            # Получаем детали товара по URL
            url = item.get('url')
            details = details_dict.get(url, {})

            # СОЗДАЕМ UNIQUE SLUG С ID
            name = item.get('name', '')
            # Берем первые 50 символов названия и добавляем ID для уникальности
            base_slug = slugify(name[:50])
            unique_slug = f"{base_slug}-{product_id}"  # Добавляем ID в конец

            # Создаем или обновляем товар
            try:
                product, created = Product.objects.get_or_create(
                    id=product_id,
                    defaults={
                        'name': name,
                        'slug': unique_slug,  # Используем уникальный slug
                        'article': item.get('article', '') or details.get('article', ''),
                        'url': url,
                        'price': item.get('price', 0),
                        'old_price': details.get('old_price'),
                        'in_stock': item.get('in_stock', False),
                        'image': item.get('image', ''),
                        'category': category,
                        'description': details.get('description', ''),
                        'meta_title': name,
                    }
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка при создании товара {product_id}: {e}'))
                continue

            # Если товар уже существует, обновляем его
            if not created:
                product.name = name
                product.price = item.get('price', product.price)
                product.old_price = details.get('old_price', product.old_price)
                product.in_stock = item.get('in_stock', product.in_stock)
                product.image = item.get('image', product.image)
                product.description = details.get('description', product.description)
                product.article = item.get('article', '') or details.get('article', '')
                product.slug = unique_slug  # Обновляем slug
                product.save()
                update_count += 1
                self.stdout.write(f'🔄 Обновлен товар: {product.name}')
            else:
                success_count += 1
                self.stdout.write(f'➕ Добавлен товар: {product.name}')

            # Импортируем изображения
            images = details.get('images', [])
            if images:
                # Очищаем старые изображения
                ProductImage.objects.filter(product=product).delete()

                # Добавляем новые изображения
                unique_images = []
                seen_urls = set()
                for img_url in images:
                    if '450_450' in img_url and img_url not in seen_urls:
                        unique_images.append(img_url)
                        seen_urls.add(img_url)

                if not unique_images:
                    for img_url in images:
                        if img_url not in seen_urls:
                            unique_images.append(img_url)
                            seen_urls.add(img_url)

                for idx, img_url in enumerate(unique_images[:10]):
                    ProductImage.objects.create(
                        product=product,
                        image=img_url,
                        is_main=(idx == 0),
                        order=idx
                    )
                self.stdout.write(f'  🖼️ Добавлено {len(unique_images)} изображений')

            # Импортируем характеристики
            properties = details.get('properties', {})
            if properties:
                ProductProperty.objects.filter(product=product).delete()

                for prop_name, prop_value in properties.items():
                    if prop_value:
                        ProductProperty.objects.create(
                            product=product,
                            name=prop_name,
                            value=str(prop_value)
                        )
                self.stdout.write(f'  📋 Добавлено {len(properties)} характеристик')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Импорт завершен!\n'
            f'➕ Добавлено товаров: {success_count}\n'
            f'🔄 Обновлено товаров: {update_count}\n'
            f'⏭️ Пропущено записей: {skip_count}'
        ))