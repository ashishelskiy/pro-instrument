# catalog/management/commands/import_products.py
import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Category, Product, ProductProperty, ProductImage


class Command(BaseCommand):
    help = 'Импорт товаров из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к JSON файлу')

    def handle(self, *args, **options):
        file_path = options['file_path']

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Создаем категорию
        category, _ = Category.objects.get_or_create(
            name='Аккумуляторные шуруповерты и дрели',
            defaults={'slug': 'akkumulyatornye-shurupoverty-i-dreli'}
        )

        # Словарь для дедупликации
        seen_products = {}

        for item in data:
            # Пропускаем дубликаты (по id)
            if item.get('id') is None:
                continue

            product_id = str(item['id'])
            if product_id in seen_products:
                continue
            seen_products[product_id] = True

            # Создаем товар
            product, created = Product.objects.get_or_create(
                id=product_id,
                defaults={
                    'name': item['name'],
                    'slug': slugify(item['name'][:50]),
                    'article': item.get('article', ''),
                    'url': item['url'],
                    'price': item['price'],
                    'in_stock': item.get('in_stock', False),
                    'image': item.get('image', ''),
                    'category': category,
                    'meta_title': item['name'],
                }
            )

            if created:
                self.stdout.write(f'Добавлен товар: {product.name}')
            else:
                self.stdout.write(f'Обновлен товар: {product.name}')
                # Обновляем поля
                product.name = item['name']
                product.price = item['price']
                product.in_stock = item.get('in_stock', False)
                product.image = item.get('image', '')
                product.save()