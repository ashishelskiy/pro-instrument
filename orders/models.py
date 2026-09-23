# orders/models.py
from django.db import models
from django.conf import settings


class DeliveryMethod(models.Model):
    """Способ доставки."""
    name = models.CharField('Название', max_length=255)
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Краткое описание способа доставки (показывается клиенту)',
    )
    price = models.DecimalField(
        'Стоимость',
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='0 = бесплатно. Если стоимость рассчитывается индивидуально — оставьте 0 и напишите в описании',
    )
    is_active = models.BooleanField('Активен', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Способ доставки'
        verbose_name_plural = 'Способы доставки'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Order(models.Model):
    """Заказ."""
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    )

    PAYMENT_CHOICES = (
        ('cash', 'Наличными при получении'),
        ('card', 'Картой онлайн'),
        ('invoice', 'По счёту (для юрлиц)'),
    )

    # Кто заказал
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Пользователь',
    )

    # От чьей организации (если есть)
    organization = models.ForeignKey(
        'users.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Организация',
    )

    # Контакт
    name = models.CharField('Имя', max_length=150)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')

    # Доставка — ссылка на модель
    delivery_method = models.ForeignKey(
        DeliveryMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Способ доставки',
    )
    # Снимок данных на момент заказа
    delivery_method_name = models.CharField(
        'Способ доставки (снимок)',
        max_length=255,
        blank=True,
        help_text='Сохраняется на момент оформления заказа',
    )
    delivery_price = models.DecimalField(
        'Стоимость доставки',
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    # Адрес доставки
    address = models.TextField('Адрес доставки', blank=True)

    # Оплата
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='cash',
    )

    # Комментарий
    comment = models.TextField('Комментарий', blank=True)

    # Статус
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
    )

    # Итоги
    total_price = models.DecimalField(
        'Итого',
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ №{self.pk} от {self.created_at:%d.%m.%Y}'

    @property
    def is_company_order(self):
        return self.organization is not None


class OrderItem(models.Model):
    """Позиция заказа."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Товар',
    )
    # Снимок данных товара на момент заказа
    product_name = models.CharField('Название товара', max_length=500)
    product_article = models.CharField('Артикул', max_length=100, blank=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'
        ordering = ['id']

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity