from django import forms
from django.contrib import admin
from django.db import transaction
from django.utils.html import format_html
from .models import Invoice, InvoiceItem, Supplier
from .parser import parse_invoice_pdf


# Кастомная форма для удобного ввода количества (шаг 1, а не 0.001)
class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = '__all__'
        widgets = {
            'shipped_quantity': forms.NumberInput(attrs={'step': 'any', 'min': '0'}),
            'quantity': forms.NumberInput(attrs={'step': 'any', 'min': '0'}),
        }


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    form = InvoiceItemForm
    extra = 0
    fields = (
        'row_no', 'code', 'name', 'quantity', 'price', 'amount',
        'shipped_quantity', 'shipment_date', 'manager_comment', 'shipment_status_col', 'product'
    )
    readonly_fields = ('row_no', 'shipment_status_col')
    autocomplete_fields = ('product',)

    @admin.display(description='Статус')
    def shipment_status_col(self, obj):
        if not obj.pk:
            return '—'
        if obj.is_fully_shipped:
            return format_html('<span style="color: green; font-weight: bold;">✔ Отгружено</span>')
        elif obj.is_partially_shipped:
            return format_html('<span style="color: orange; font-weight: bold;">◑ Частично</span>')
        return format_html('<span style="color: gray;">— Не отгружено</span>')


# @admin.register(Supplier)
# class SupplierAdmin(admin.ModelAdmin):
#     list_display = ('name', 'inn', 'kpp')
#     search_fields = ('name', 'inn')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'supplier', 'buyer_name', 'total', 'parsed_ok')
    list_filter = ('parsed_ok', 'date')
    search_fields = ('number', 'supplier__name', 'buyer_name', 'buyer_inn')
    readonly_fields = ('parsed_ok', 'parse_log')
    inlines = [InvoiceItemInline]

    fieldsets = (
        ('Файл', {'fields': ('pdf_file',)}),
        ('Счёт', {'fields': ('number', 'date')}),
        ('Покупатель', {'fields': ('organization', 'user', 'buyer_name', 'buyer_inn', 'buyer_kpp')}),
        ('Заказ', {'fields': ('order',)}),
        ('Суммы', {'fields': ('total', 'vat_total')}),
        ('Служебное', {'fields': ('parsed_ok', 'parse_log')}),
        ('Отгрузка и доставка', {
            'fields': ('delivery_status', 'delivery_date', 'manager_comment')
        }),
    )

    def save_model(self, request, obj, form, change):
        # 1. Если файл загружен и счёт ещё не разобран
        if obj.pdf_file and not obj.parsed_ok:
            # Сначала сохраняем объект, чтобы Django физически записал PDF на диск
            super().save_model(request, obj, form, change)

            # Теперь файл точно есть по пути obj.pdf_file.path, парсим его
            data = parse_invoice_pdf(obj.pdf_file.path)
            errors = list(data['errors'])

            obj.number = data['number'] or obj.number
            obj.date = data['date'] or obj.date
            obj.total = data['total']
            obj.vat_total = data['vat_total']
            obj.buyer_name = data['buyer'].get('name', '')
            obj.buyer_inn = data['buyer'].get('inn', '')
            obj.buyer_kpp = data['buyer'].get('kpp', '')

            # Поставщик
            if data['supplier'].get('inn'):
                sup, _ = Supplier.objects.get_or_create(
                    inn=data['supplier']['inn'],
                    defaults={
                        'name': data['supplier'].get('name', ''),
                        'kpp': data['supplier'].get('kpp', ''),
                    },
                )
                obj.supplier = sup

            # Организация-покупатель
            if data['buyer'].get('inn'):
                from users.models import Organization
                org = Organization.objects.filter(inn=data['buyer']['inn']).first()
                if org:
                    obj.organization = org
                    obj.user = org.user
                else:
                    errors.append(
                        f'Организация с ИНН {data["buyer"]["inn"]} не найдена в БД'
                    )

            # Дубли
            if Invoice.objects.filter(
                    number=obj.number, date=obj.date
            ).exclude(pk=obj.pk).exists():
                errors.append('Счёт с таким номером и датой уже существует')

            obj.parsed_ok = not errors
            obj.parse_log = '\n'.join(errors)

            # Сохраняем обновлённые поля (номер, дату, суммы)
            obj.save()

            # Создаём товары (счёт уже есть в базе, можно привязывать)
            if not obj.items.exists():
                from catalog.models import Product
                for it in data['items']:
                    product = None
                    if it['code']:
                        matches = Product.objects.filter(article=it['code'])
                        if matches.count() == 1:
                            product = matches.first()
                        elif matches.count() > 1:
                            errors.append(f'Найдено несколько товаров с артикулом {it["code"]}')
                        else:
                            errors.append(f'Товар с артикулом {it["code"]} не найден')

                    InvoiceItem.objects.create(
                        invoice=obj,
                        product=product,
                        row_no=it['row_no'],
                        code=it['code'],
                        name=it['name'],
                        quantity=it['quantity'],
                        price=it['price'],
                        vat_rate=it['vat_rate'],
                        vat_amount=it['vat_amount'],
                        amount=it['amount'],
                    )
        else:
            # Если файла нет или он уже разобран — просто сохраняем
            super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # 1) Сначала сохраняем инлайны (позиции счёта)
        super().save_related(request, form, formsets, change)

        # 2) Теперь у счёта актуальные items — пересчитываем статус
        obj = form.instance
        items = obj.items.all()
        if not items.exists():
            return

        all_shipped = all(i.is_fully_shipped for i in items)
        none_shipped = all(i.shipped_quantity == 0 for i in items)

        if all_shipped:
            new_status = 'shipped'
        elif none_shipped:
            new_status = 'pending'
        else:
            new_status = 'partial'

        if obj.delivery_status != new_status:
            obj.delivery_status = new_status
            obj.save(update_fields=['delivery_status'])