# catalog/management/commands/import_price_list.py
import openpyxl
from django.core.management.base import BaseCommand
from catalog.models import Product, Brand, Category


class Command(BaseCommand):
    help = 'Импорт прайс-листа из Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Путь к Excel файлу с прайс-листом'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Проверить данные без сохранения'
        )

    def handle(self, *args, **options):
        filename = options['file']
        dry_run = options.get('dry_run', False)

        # Загружаем Excel
        wb = openpyxl.load_workbook(filename)
        ws = wb.active

        # Счетчики
        updated = 0
        created = 0
        errors = 0

        # Читаем данные (со второй строки, первая — заголовки)
        for row in ws.iter_rows(min_row=2, values_only=True):
            try:
                article = str(row[1]) if row[1] else ''
                name = str(row[2]) if row[2] else ''
                price = float(row[3]) if row[3] else 0
                old_price = float(row[4]) if row[4] else None
                in_stock = str(row[5]) == 'В наличии' if row[5] else True
                brand_name = str(row[6]) if row[6] else ''
                category_name = str(row[7]) if row[7] else ''

                if not article:
                    continue

                # Получаем или создаем товар по артикулу
                product, is_new = Product.objects.get_or_create(
                    article=article,
                    defaults={
                        'name': name,
                        'price': price,
                        'old_price': old_price,
                        'in_stock': in_stock,
                    }
                )

                if not is_new:
                    # Обновляем существующий товар
                    product.name = name
                    product.price = price
                    product.old_price = old_price
                    product.in_stock = in_stock

                # Обновляем бренд
                if brand_name:
                    brand, _ = Brand.objects.get_or_create(name=brand_name)
                    product.brand = brand

                # Обновляем категорию
                if category_name:
                    category, _ = Category.objects.get_or_create(name=category_name)
                    product.category = category

                if not dry_run:
                    product.save()

                if is_new:
                    created += 1
                else:
                    updated += 1

                self.stdout.write(f"{'✅' if not dry_run else '🔍'} {article}: {name} -> {price} ₽")

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка в строке: {str(e)}')
                )

        # Итог
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 РЕЖИМ ПРОВЕРКИ (dry-run)'))
        self.stdout.write(self.style.SUCCESS(f'\n📊 ИТОГО:'))
        self.stdout.write(f'  Создано: {created}')
        self.stdout.write(f'  Обновлено: {updated}')
        self.stdout.write(f'  Ошибок: {errors}')