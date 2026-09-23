# banners/models.py
from django.db import models
from django.urls import reverse
from django.utils import timezone


class BannerPosition(models.TextChoices):
    HOME_TOP = 'home_top', 'Главная — верхний слайдер'
    HOME_MIDDLE = 'home_middle', 'Главная — середина'
    CATEGORY_TOP = 'category_top', 'Категория — верх'
    SIDEBAR = 'sidebar', 'Боковая колонка'


class BannerQuerySet(models.QuerySet):
    def active(self):
        """Только активные и попадающие в период показа."""
        now = timezone.now()
        return self.filter(
            is_active=True,
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now),
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now),
        )

    def for_position(self, position):
        return self.active().filter(position=position)


class Banner(models.Model):
    title = models.CharField('Название', max_length=255, blank=True)
    description = models.TextField('Описание', blank=True)

    image = models.ImageField(
        'Изображение',
        upload_to='slider/',
        help_text='Рекомендуется 1920×600 для верхнего слайдера',
    )
    image_mobile = models.ImageField(
        'Изображение (мобильное)',
        upload_to='slider/',
        null=True, blank=True,
        help_text='Необязательно. Показывается на экранах < 768px.',
    )

    # Куда ведёт — три варианта, приоритет: category → product → link
    link = models.URLField(
        'Внешняя ссылка', blank=True,
        help_text='Используется, если не выбраны категория или товар',
    )
    category = models.ForeignKey(
        'catalog.Category',
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='banners',
    )
    product = models.ForeignKey(
        'catalog.Product',
        verbose_name='Товар',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='banners',
    )

    position = models.CharField(
        'Позиция', max_length=30,
        choices=BannerPosition.choices,
        default=BannerPosition.HOME_TOP,
    )
    sort_order = models.PositiveIntegerField(
        'Порядок', default=0,
        help_text='Чем меньше — тем раньше в слайдере',
    )

    is_active = models.BooleanField('Активен', default=True)
    start_date = models.DateTimeField('Начало показа', null=True, blank=True)
    end_date = models.DateTimeField('Конец показа', null=True, blank=True)

    # Аналитика
    views_count = models.PositiveIntegerField('Показов', default=0, editable=False)
    clicks_count = models.PositiveIntegerField('Кликов', default=0, editable=False)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    objects = BannerQuerySet.as_manager()

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title or f'Баннер #{self.pk}'

    @property
    def is_current(self):
        """Попадает ли баннер в период показа прямо сейчас."""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True

    def get_link(self):
        """Единая точка получения URL — используется в шаблоне."""
        if self.category_id:
            return self.category.get_absolute_url()
        if self.product_id:
            return self.product.get_absolute_url()
        return self.link or '#'

    def get_click_url(self):
        """URL-обёртка, которая считает клик и редиректит на get_link()."""
        return reverse('banners:click', kwargs={'pk': self.pk})