# catalog/management/commands/fill_dimensions.py
import re
from django.core.management.base import BaseCommand
from catalog.models import Product

class Command(BaseCommand):
    help = 'Заполняет поля weight, length, width, height из характеристик'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        updated = 0
        no_weight = 0
        no_dims = 0

        for product in products:
            changed = False

            # 1. Ищем вес (используем точное совпадение)
            weight_prop = product.properties.filter(name='Вес, кг').first()
            if weight_prop:
                val_str = weight_prop.value.replace(',', '.')
                numbers = re.findall(r'\d+\.?\d*', val_str)
                if numbers:
                    val = float(numbers[0])
                    # Если в значении есть "кг" или "kg" — умножаем на 1000
                    if 'кг' in val_str.lower() or 'kg' in val_str.lower():
                        product.weight = int(val * 1000)
                    else:
                        # Если единицы не указаны, предполагаем, что это кг
                        product.weight = int(val * 1000)
                    changed = True
            else:
                no_weight += 1

            # 2. Ищем габариты (используем точное совпадение)
            dims_prop = product.properties.filter(name='Габариты упаковки').first()
            if dims_prop:
                val_str = dims_prop.value.replace(',', '.')
                numbers = re.findall(r'\d+\.?\d*', val_str)
                if len(numbers) >= 3:
                    l, w, h = float(numbers[0]), float(numbers[1]), float(numbers[2])
                    # Если в строке есть "м" (но не "мм"), переводим в см
                    if 'м' in val_str.lower() and 'мм' not in val_str.lower():
                        l, w, h = l * 100, w * 100, h * 100
                    # Если "мм", переводим в см
                    elif 'мм' in val_str.lower():
                        l, w, h = l / 10, w / 10, h / 10
                    product.length = int(l)
                    product.width = int(w)
                    product.height = int(h)
                    changed = True
            else:
                no_dims += 1

            if changed:
                product.save(update_fields=['weight', 'length', 'width', 'height'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Обновлено товаров: {updated}'))
        self.stdout.write(self.style.WARNING(f'Без характеристики «Вес, кг»: {no_weight}'))
        self.stdout.write(self.style.WARNING(f'Без характеристики «Габариты упаковки»: {no_dims}'))