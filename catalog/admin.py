# catalog/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, CharWidget
from .models import (
    Category, Brand, Product, ProductImage,
    ProductProperty, CategoryProperty, ProductCertificate,
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


class ProductCertificateInline(admin.TabularInline):
    model = ProductCertificate
    extra = 1
    fields = ('name', 'file', 'url', 'number', 'valid_until', 'sort_order')
    ordering = ('sort_order',)


class CategoryPropertyInline(admin.TabularInline):
    model = CategoryProperty
    extra = 1
    fields = ('name', 'is_required', 'sort_order')
    ordering = ('sort_order', 'name')


class PriceUpdateResource(resources.ModelResource):
    """Ресурс для импорта/обновления товаров."""

    external_id = fields.Field(
        column_name='external_id', attribute='external_id', widget=CharWidget(),
    )
    article = fields.Field(
        column_name='article', attribute='article', widget=CharWidget(),
    )
    name = fields.Field(column_name='name', attribute='name', widget=CharWidget())
    price = fields.Field(column_name='price', attribute='price')
    old_price = fields.Field(column_name='old_price', attribute='old_price', default=None)
    in_stock = fields.Field(column_name='in_stock', attribute='in_stock')
    brand__name = fields.Field(
        column_name='brand__name',
        attribute='brand',
        widget=ForeignKeyWidget(Brand, field='name'),
    )
    category__name = fields.Field(
        column_name='category__name',
        attribute='category',
        widget=ForeignKeyWidget(Category, field='name'),
    )
    image = fields.Field(column_name='image', attribute='image', widget=CharWidget())
    description = fields.Field(
        column_name='description', attribute='description', default='', widget=CharWidget(),
    )

    class Meta:
        model = Product
        fields = (
            'external_id',
            'article',
            'name',
            'price',
            'old_price',
            'in_stock',
            'brand__name',
            'category__name',
            'image',
            'description',
        )
        export_order = fields
        import_id_fields = ['article']      # ключ обновления — артикул
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

    def before_import_row(self, row, **kwargs):
        # Наличие
        val = row.get('in_stock')
        if isinstance(val, str):
            row['in_stock'] = val.strip() in ('True', 'true', 'В наличии', '1')
        elif val is None:
            row['in_stock'] = True

        # Пустые FK — не пытаемся их создать
        if not row.get('brand__name'):
            row.pop('brand__name', None)
        if not row.get('category__name'):
            row.pop('category__name', None)

        # Пустое описание
        if not row.get('description'):
            row['description'] = ''

        return row

    def after_import_row(self, row, row_result, **kwargs):
        """Дополнительное обновление цены/наличия, если запись обновляется."""
        if row_result.import_type == 'update':
            try:
                product = Product.objects.get(article=row['article'])
                product.price = row['price']
                product.in_stock = row['in_stock']
                if row.get('old_price'):
                    product.old_price = row['old_price']
                product.save()
                row_result.object = product
            except Product.DoesNotExist:
                pass

    def dehydrate_in_stock(self, product):
        return 'True' if product.in_stock else 'False'


# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'parent', 'created_at')
#     list_filter = ('parent',)
#     search_fields = ('name', 'slug')
#     prepopulated_fields = {'slug': ('name',)}
#     ordering = ('name',)
#     inlines = [CategoryPropertyInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'show_in_bento', 'bento_order', 'created_at')
    list_filter = ('parent', 'show_in_bento')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    list_editable = ('show_in_bento', 'bento_order')
    inlines = [CategoryPropertyInline]
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'parent', 'description')
        }),
        ('Медиа', {
            'fields': ('image', 'bento_image', 'icon')
        }),
        ('Bento на главной', {
            'fields': ('show_in_bento', 'bento_order'),
            'description': 'Отметьте до 6 категорий для сетки карточек на главной. '
                           'Если отметить больше — покажутся первые 6 по порядку.'
        }),
        ('Системные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_featured', 'sort_order', 'product_count')
    list_filter = ('is_featured',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_featured', 'sort_order')
    ordering = ('sort_order', 'name')

    @admin.display(description='Товаров')
    def product_count(self, obj):
        return obj.product_count


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = PriceUpdateResource

    list_display = (
        'name', 'article', 'price', 'old_price', 'in_stock', 'brand', 'category',
    )
    list_filter = ('in_stock', 'brand', 'category')
    search_fields = ('name', 'article', 'external_id', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    inlines = [ProductCertificateInline, ProductImageInline, ProductPropertyInline]
    list_editable = ['price', 'old_price', 'in_stock']

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name', 'slug', 'article',
                'price', 'old_price', 'in_stock',
                'image', 'image_preview',
                'brand', 'category',
            ),
        }),
        ('Сертификация', {
            'fields': ('no_certificate_required',),
            'description': 'Сертификаты добавляются ниже в блоке «Сертификаты товаров». '
                           'Если товар не подлежит сертификации — поставьте галочку.',
        }),
        ('Описание', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',),
        }),
        ('Служебное (для импорта)', {
            'fields': ('external_id',),
            'classes': ('collapse',),
            'description': 'Заполняется автоматически при импорте. '
                           'При ручном добавлении можно оставить пустым.',
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Превью')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 120px;" />',
                obj.image.url,
            )
        return '—'


@admin.register(ProductCertificate)
class ProductCertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_link', 'number', 'valid_until', 'has_file')
    list_filter = ('valid_until',)
    search_fields = ('name', 'number', 'product__name', 'product__article')
    list_per_page = 50
    date_hierarchy = 'valid_until'
    ordering = ('-valid_until',)
    autocomplete_fields = ('product',)

    @admin.display(description='Товар')
    def product_link(self, obj):
        url = reverse('admin:catalog_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    @admin.display(description='Файл', boolean=True)
    def has_file(self, obj):
        return bool(obj.file)



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