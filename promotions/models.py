from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Promotion(models.Model):
    """Акция — подборка товаров."""
    title = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL', max_length=255, unique=True, blank=True)
    description = models.TextField('Описание', blank=True)
    image = models.ImageField(
        'Изображение',
        upload_to='promotions/',
        null=True, blank=True,
        help_text='Картинка для страницы акции',
    )

    categories = models.ManyToManyField(
        'catalog.Category',
        verbose_name='Категории',
        blank=True,
        related_name='promotions',
        help_text='Все товары из этих категорий попадут в акцию',
    )
    products = models.ManyToManyField(
        'catalog.Product',
        verbose_name='Отдельные товары',
        blank=True,
        related_name='promotions',
        help_text='Эти товары добавятся сверх категорий',
    )

    is_active = models.BooleanField('Активна', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('promotions:detail', kwargs={'slug': self.slug})

    def get_products(self):
        """Все товары акции: из категорий + отдельные."""
        from catalog.models import Product
        from django.db.models import Q

        q = Q()

        if self.categories.exists():
            q |= Q(category__in=self.categories.all())

        if self.products.exists():
            q |= Q(pk__in=self.products.values_list('pk', flat=True))

        if not q:
            return Product.objects.none()

        return Product.objects.filter(q, in_stock=True).distinct()