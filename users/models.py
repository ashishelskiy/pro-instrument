# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')

    GENDER_CHOICES = (
        ('M', 'Мужской'),
        ('F', 'Женский'),
        ('', 'Не указан'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, default='', verbose_name='Пол')
    birth_date = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    middle_name = models.CharField(max_length=150, blank=True, verbose_name='Отчество')

    # Согласие на обработку персональных данных
    agree_to_terms = models.BooleanField('Согласие на обработку ПД', default=False)
    agreed_at = models.DateTimeField('Дата согласия', null=True, blank=True)

    def __str__(self):
        return self.email or self.username

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(p for p in parts if p).strip() or self.username

    @property
    def default_organization(self):
        return self.organizations.filter(is_default=True).first()

    def get_display_name(self):
        first = (self.first_name or '').strip()
        last = (self.last_name or '').strip()
        if first and last:
            return f'{first} {last[0]}.'
        if first:
            return first
        if last:
            return last
        return self.username

    def get_header_name(self):
        org = self.default_organization
        if org:
            return org.short_name
        return self.get_display_name()

    def get_header_subtitle(self):
        org = self.default_organization
        if org:
            return f'ИНН {org.inn}'
        return ''

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Organization(models.Model):
    ORG_TYPE_CHOICES = (
        ('ooo', 'ООО'),
        ('ip', 'ИП'),
    )
    org_type = models.CharField(max_length=3, choices=ORG_TYPE_CHOICES, default='ooo', verbose_name='Тип организации')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizations', verbose_name='Владелец')
    is_default = models.BooleanField(default=False, verbose_name='Основная организация')

    name = models.CharField(max_length=255, verbose_name='Название организации')
    inn = models.CharField(max_length=12, verbose_name='ИНН')
    kpp = models.CharField(max_length=9, blank=True, verbose_name='КПП')
    ogrn = models.CharField(max_length=15, blank=True, verbose_name='ОГРН / ОГРНИП')
    address = models.TextField(verbose_name='Юридический адрес')
    actual_address = models.TextField(blank=True, verbose_name='Фактический адрес')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    director = models.CharField(max_length=255, blank=True, verbose_name='Директор')
    bank_name = models.CharField(max_length=255, blank=True, verbose_name='Банк')
    bik = models.CharField(max_length=9, blank=True, verbose_name='БИК')
    account = models.CharField(max_length=20, blank=True, verbose_name='Расчётный счёт')
    corr_account = models.CharField(max_length=20, blank=True, verbose_name='Корр. счёт')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_ip(self):
        return self.org_type == 'ip'

    @property
    def is_ooo(self):
        return self.org_type == 'ooo'

    def save(self, *args, **kwargs):
        if self.is_default and self.user_id:
            Organization.objects.filter(user_id=self.user_id, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    SHORT_NAME_LIMIT = 10

    @property
    def short_name(self):
        name = (self.name or '').strip()
        if len(name) <= self.SHORT_NAME_LIMIT:
            return name
        return name[:self.SHORT_NAME_LIMIT].rstrip() + '…'

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'
        ordering = ['-is_default', 'name']


class Favorite(models.Model):
    """Избранные товары пользователя."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Товар',
    )
    added_at = models.DateTimeField('Добавлен', auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user} → {self.product}'


class StockNotification(models.Model):
    """Подписка на уведомление о поступлении товара."""
    email = models.EmailField('Email')
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='stock_notifications',
        verbose_name='Товар',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_notifications',
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    notified = models.BooleanField('Уведомлён', default=False)
    notified_at = models.DateTimeField('Дата уведомления', null=True, blank=True)

    class Meta:
        verbose_name = 'Подписка на поступление'
        verbose_name_plural = 'Подписки на поступление'
        ordering = ['-created_at']
        unique_together = ('email', 'product')

    def __str__(self):
        return f'{self.email} → {self.product}'


class PriceRequest(models.Model):
    """Заявка на запрос цены на товар, отсутствующий в каталоге."""
    name = models.CharField('Имя', max_length=150)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')
    description = models.TextField(
        'Описание товара',
        help_text='Опишите, какой товар вам нужен: название, модель, характеристики',
    )
    comment = models.TextField('Комментарий', blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='price_requests',
        verbose_name='Пользователь',
    )

    STATUS_CHOICES = (
        ('new', 'Новая'),
        ('in_progress', 'В обработке'),
        ('answered', 'Отвечено'),
        ('closed', 'Закрыта'),
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
    )

    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Заявка на цену'
        verbose_name_plural = 'Заявки на цену'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.description[:50]}'


class ViewedProduct(models.Model):
    """Просмотренный товар."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='viewed_products',
        verbose_name='Пользователь',
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='viewed_by',
        verbose_name='Товар',
    )
    viewed_at = models.DateTimeField('Просмотрен', auto_now=True)

    class Meta:
        verbose_name = 'Просмотренный товар'
        verbose_name_plural = 'Просмотренные товары'
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']

    def __str__(self):
        return f'{self.user} → {self.product}'


class Comparison(models.Model):
    """Товар в сравнении."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comparison_items',
        verbose_name='Пользователь',
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='in_comparisons',
        verbose_name='Товар',
    )
    added_at = models.DateTimeField('Добавлен', auto_now_add=True)

    class Meta:
        verbose_name = 'Товар в сравнении'
        verbose_name_plural = 'Сравнение товаров'
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user} → {self.product}'