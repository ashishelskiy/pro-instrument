# catalog/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, CharWidget
from .models import (
    Category, Brand, Product, ProductImage,
    ProductProperty, CategoryProperty
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_main', 'order')
    ordering = ('order',)


class ProductPropertyInline(admin.TabularInline):
    model = ProductProperty
    extra = 1
    fields = ('name', 'value')


# ===== РЕСУРС ТОЛЬКО ДЛЯ ОБНОВЛЕНИЯ ЦЕН И НАЛИЧИЯ =====
class PriceUpdateResource(resources.ModelResource):
    id = fields.Field(column_name='id', attribute='id', widget=CharWidget())
    article = fields.Field(column_name='article', attribute='article', widget=CharWidget())
    name = fields.Field(column_name='name', attribute='name', widget=CharWidget())
    price = fields.Field(column_name='price', attribute='price')
    old_price = fields.Field(column_name='old_price', attribute='old_price', default=None)
    in_stock = fields.Field(column_name='in_stock', attribute='in_stock')
    brand__name = fields.Field(
        column_name='brand__name',
        attribute='brand',
        widget=ForeignKeyWidget(Brand, field='name')
    )
    category__name = fields.Field(
        column_name='category__name',
        attribute='category',
        widget=ForeignKeyWidget(Category, field='name')
    )
    image = fields.Field(column_name='image', attribute='image', widget=CharWidget())
    description = fields.Field(column_name='description', attribute='description', default='', widget=CharWidget())
    url = fields.Field(column_name='url', attribute='url', widget=CharWidget())

    class Meta:
        model = Product
        fields = (
            'id',
            'article',
            'name',
            'price',
            'old_price',
            'in_stock',
            'brand__name',
            'category__name',
            'image',
            'description',
            'url',
        )
        export_order = fields
        import_id_fields = ['article']
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

    def before_import_row(self, row, **kwargs):
        """Подготавливаем данные перед импортом"""
        # Конвертируем статус наличия
        if row.get('in_stock') == 'True':
            row['in_stock'] = True
        elif row.get('in_stock') == 'False':
            row['in_stock'] = False
        elif isinstance(row.get('in_stock'), str):
            row['in_stock'] = row['in_stock'].strip() in ('True', 'true', 'В наличии', '1')

        # Если бренд не указан — пропускаем
        if not row.get('brand__name') or row['brand__name'] == '':
            row.pop('brand__name', None)

        # Если категория не указана — пропускаем
        if not row.get('category__name') or row['category__name'] == '':
            row.pop('category__name', None)

        # Пустое описание
        if not row.get('description'):
            row['description'] = ''

        return row

    def after_import_row(self, row, row_result, **kwargs):
        """Обновляем только цену и наличие"""
        if row_result.import_type == 'update':
            try:
                product = Product.objects.get(article=row['article'])
                product.price = row['price']
                product.in_stock = row['in_stock']

                # ← ИСПРАВЛЕНО: обновляем old_price только если есть значение
                if row.get('old_price') and row.get('old_price') != '':
                    product.old_price = row['old_price']
                # Если old_price пустая — НЕ ТРОГАЕМ

                product.save()
                row_result.object = product
            except Product.DoesNotExist:
                pass

    def dehydrate_in_stock(self, product):
        return 'True' if product.in_stock else 'False'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = PriceUpdateResource
    list_display = ('id', 'name', 'article', 'price', 'old_price', 'in_stock', 'brand', 'category')
    list_filter = ('in_stock', 'brand', 'category')
    search_fields = ('id', 'name', 'article', 'url')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductImageInline, ProductPropertyInline]
    list_editable = ['price', 'old_price', 'in_stock']
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'name', 'slug', 'article', 'url', 'price', 'old_price',
                       'in_stock', 'image', 'brand', 'category')
        }),
        ('Описание', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductProperty)
class ProductPropertyAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value')
    list_filter = ('name',)
    search_fields = ('product__name', 'name', 'value')


@admin.register(CategoryProperty)
class CategoryPropertyAdmin(admin.ModelAdmin):
    list_display = ('category', 'name', 'is_required', 'sort_order')
    list_filter = ('category', 'is_required')
    search_fields = ('name',)