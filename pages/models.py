# pages/models.py
from django.db import models
from django.utils import timezone


class Page(models.Model):
    """Статическая страница (О компании, Доставка, Контакты)."""
    slug = models.SlugField(
        'URL',
        max_length=100,
        unique=True,
        help_text='Например: about, delivery, contacts',
    )
    title = models.CharField('Заголовок', max_length=255)
    content = models.TextField('Содержимое', help_text='Поддерживается HTML')
    meta_title = models.CharField('Meta Title', max_length=255, blank=True)
    meta_description = models.TextField('Meta Description', max_length=500, blank=True)

    is_published = models.BooleanField('Опубликована', default=True)

    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'
        ordering = ['title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('pages:page_detail', kwargs={'slug': self.slug})


class News(models.Model):
    """Новость."""
    slug = models.SlugField('URL', max_length=200, unique=True, blank=True)
    title = models.CharField('Заголовок', max_length=255)
    short_description = models.TextField(
        'Краткое описание',
        max_length=500,
        blank=True,
        help_text='Для списка новостей и SEO',
    )
    content = models.TextField('Полный текст', help_text='Поддерживается HTML')
    image = models.ImageField(
        'Изображение',
        upload_to='news/',
        null=True,
        blank=True,
    )

    is_published = models.BooleanField('Опубликована', default=True)
    published_at = models.DateTimeField('Дата публикации', default=timezone.now)

    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)[:200]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('pages:news_detail', kwargs={'slug': self.slug})


class SiteSettings(models.Model):
    """Глобальные настройки сайта. Должна быть одна запись."""
    site_name = models.CharField(
        'Название сайта',
        max_length=255,
        default='PRO-инструмент',
    )
    site_description = models.TextField(
        'Описание сайта',
        max_length=500,
        blank=True,
        help_text='Для SEO — meta description по умолчанию',
    )
    phone = models.CharField('Телефон', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    admin_email = models.EmailField(
        'Email для уведомлений',
        blank=True,
        help_text='Куда приходят уведомления о заказах и заявках',
    )
    address = models.TextField('Адрес', blank=True)
    work_hours = models.CharField('Часы работы', max_length=255, blank=True)

    # Реквизиты
    company_name = models.CharField('Название организации', max_length=255, blank=True)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    ogrn = models.CharField('ОГРН', max_length=15, blank=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)

    # Соцсети
    vk_url = models.URLField('ВКонтакте', blank=True)
    telegram_url = models.URLField('Telegram', blank=True)
    whatsapp_url = models.URLField('WhatsApp', blank=True)

    # Логотип
    logo = models.ImageField('Логотип', upload_to='site/', null=True, blank=True)

    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Singleton — только одна запись
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Получить единственную запись (или создать пустую)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj