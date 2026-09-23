from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


# class Category(models.Model):
#     """Модель категории товаров"""
#     name = models.CharField('Название', max_length=255)
#     slug = models.SlugField('URL', max_length=255, unique=True, blank=True)
#     parent = models.ForeignKey(
#         'self',
#         on_delete=models.CASCADE,
#         verbose_name='Родительская категория',
#         null=True,
#         blank=True,
#         related_name='children'
#     )
#     created_at = models.DateTimeField('Дата создания', auto_now_add=True)
#     updated_at = models.DateTimeField('Дата обновления', auto_now=True)
#
#     class Meta:
#         verbose_name = 'Категория'
#         verbose_name_plural = 'Категории'
#         ordering = ['name']
#
#     def __str__(self):
#         return self.name
#
#     def get_absolute_url(self):
#         return reverse('catalog:category_detail', kwargs={'slug': self.slug})


class Category(models.Model):
    """Модель категории товаров"""
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL', max_length=255, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        verbose_name='Родительская категория',
        null=True,
        blank=True,
        related_name='children'
    )
    # НОВЫЕ ПОЛЯ ДЛЯ КАРТИНОК И ИКОНОК
    image = models.ImageField(
        'Изображение категории',
        upload_to='categories/',
        null=True,
        blank=True,
        help_text='Загрузите изображение для категории (рекомендуемый размер: 400x400)'
    )
    bento_image = models.ImageField(
        'Изображение для bento',
        upload_to='bento/',
        null=True, blank=True,
        help_text='Отдельная картинка для bento-сетки на главной. '
                  'Размер зависит от позиции: большая — 468×185, '
                  'маленькая — 224×185. Если не загружена — используется основная.',
    )
    icon = models.CharField(
        'Иконка (Font Awesome)',
        max_length=50,
        blank=True,
        default='fa-folder-open',
        help_text='Выберите иконку из Font Awesome: fa-drill, fa-hammer, fa-saw, fa-tools и т.д.'
    )
    description = models.TextField('Описание', blank=True, max_length=500)  # Опционально
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})

    description = models.TextField('Описание', blank=True, max_length=500)

    # ===== BENTO НА ГЛАВНОЙ =====
    show_in_bento = models.BooleanField(
        'Показывать в bento на главной',
        default=False,
        help_text='Отметьте до 6 категорий для сетки карточек на главной. '
                  'Если отметить больше — покажутся первые 6 по порядку.',
    )
    bento_order = models.PositiveIntegerField(
        'Порядок в bento',
        default=0,
        help_text='Чем меньше — тем раньше. Только для категорий с галочкой выше.',
    )

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

class Brand(models.Model):
    """Модель бренда"""
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL', max_length=255, unique=True, blank=True)
    logo = models.ImageField('Логотип', upload_to='brands/', null=True, blank=True)
    description = models.TextField('Описание', blank=True, max_length=500)
    is_featured = models.BooleanField(
        'Показывать на главной',
        default=False,
        help_text='Отметьте, чтобы бренд появился в блоке «Бренды» на главной странице',
    )
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:brand_detail', kwargs={'slug': self.slug})

    @property
    def product_count(self):
        """Количество товаров в наличии."""
        return self.products.filter(in_stock=True).count()


class Product(models.Model):
    """Модель товара"""

    # ===== СЛУЖЕБНОЕ (для будущего парсера) =====
    external_id = models.CharField(
        'ID товара у поставщика',
        max_length=50,
        blank=True,
        db_index=True,
        help_text='Заполняется автоматически при импорте. При ручном добавлении можно оставить пустым.',
    )

    # ===== ОСНОВНОЕ =====
    name = models.CharField('Название', max_length=500)
    slug = models.SlugField('URL', max_length=500, unique=True, blank=True)
    article = models.CharField('Артикул', max_length=100, blank=True, db_index=True)

    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        'Старая цена', max_digits=10, decimal_places=2, null=True, blank=True,
    )
    in_stock = models.BooleanField('В наличии', default=True)

    image = models.ImageField(
        'Главное изображение',
        upload_to='products/',
        blank=True,
        null=True,
        help_text='Рекомендуемый размер: 800x800',
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        verbose_name='Бренд',
        null=True,
        blank=True,
        related_name='products',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
        null=True,
        blank=True,
        related_name='products',
    )
    description = models.TextField('Описание', blank=True)

    # ===== СЕРТИФИКАЦИЯ =====
    no_certificate_required = models.BooleanField(
        'Не подлежит сертификации',
        default=False,
        help_text='Отметьте, если товар не подлежит обязательной сертификации',
    )

    # ===== СИСТЕМНЫЕ =====
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    # ===== SEO =====
    meta_title = models.CharField('Meta Title', max_length=255, blank=True)
    meta_description = models.TextField('Meta Description', max_length=500, blank=True)
    meta_keywords = models.CharField('Meta Keywords', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['price']),
            models.Index(fields=['in_stock']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:450] or 'product'
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f'{base_slug}-{counter}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def sales_count(self):
        """Количество проданных единиц (из заказов)."""
        from orders.models import OrderItem
        from django.db.models import Sum
        result = OrderItem.objects.filter(product=self).aggregate(total=Sum('quantity'))
        return result['total'] or 0


class ProductImage(models.Model):
    """Модель изображений товара"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар',
        related_name='images'
    )
    image = models.ImageField('Изображение', upload_to='products/gallery/')
    is_main = models.BooleanField('Главное изображение', default=False)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['order', 'id']

    def __str__(self):
        return f'Изображение для {self.product.name}'


class ProductProperty(models.Model):
    """Модель характеристик товара"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар',
        related_name='properties'
    )
    name = models.CharField('Название характеристики', max_length=255)
    value = models.CharField('Значение', max_length=500)

    class Meta:
        verbose_name = 'Характеристика товара'
        verbose_name_plural = 'Характеристики товаров'
        unique_together = ['product', 'name']
        indexes = [
            models.Index(fields=['name', 'value']),
        ]

    def __str__(self):
        return f'{self.name}: {self.value}'


class CategoryProperty(models.Model):
    """Шаблон характеристик для категории"""
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name='Категория',
        related_name='property_templates'
    )
    name = models.CharField('Название характеристики', max_length=255)
    is_required = models.BooleanField('Обязательная', default=False)
    sort_order = models.PositiveIntegerField('Порядок сортировки', default=0)

    class Meta:
        verbose_name = 'Шаблон характеристики'
        verbose_name_plural = 'Шаблоны характеристик'
        ordering = ['sort_order', 'name']
        unique_together = ['category', 'name']

    def __str__(self):
        return f'{self.category.name}: {self.name}'


class ProductCertificate(models.Model):
    """Сертификат товара. У одного товара может быть несколько."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Товар',
    )
    name = models.CharField(
        'Название документа',
        max_length=255,
        help_text='Например: «Сертификат соответствия», «Декларация соответствия»',
    )
    file = models.FileField(
        'Файл',
        upload_to='certificates/',
        null=True,
        blank=True,
        help_text='PDF, JPG или PNG',
    )
    url = models.URLField(
        'Ссылка на реестр',
        max_length=500,
        blank=True,
        help_text='Ссылка на запись в реестре Росаккредитации',
    )
    number = models.CharField(
        'Номер документа',
        max_length=100,
        blank=True,
        help_text='Номер сертификата или декларации (если известен)',
    )
    valid_until = models.DateField(
        'Действителен до',
        null=True,
        blank=True,
    )
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Сертификат товара'
        verbose_name_plural = 'Сертификаты товаров'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.product.name} — {self.name}'