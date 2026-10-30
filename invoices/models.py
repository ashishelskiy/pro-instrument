from django.db import models


class Supplier(models.Model):
    name = models.CharField('Название', max_length=255)
    inn = models.CharField('ИНН', max_length=12, unique=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    address = models.TextField('Адрес', blank=True)
    phone = models.CharField('Телефон', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (ИНН {self.inn})'


class Invoice(models.Model):
    number = models.CharField('Номер счёта', max_length=50, blank=True)
    date = models.DateField('Дата счёта', null=True, blank=True)

    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT,
        null=True, blank=True, related_name='invoices',
        verbose_name='Поставщик',
    )

    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invoices',
        verbose_name='Пользователь (владелец счёта)',
        help_text='Для юрлиц заполняется автоматически из организации. '
                  'Для физлиц — вручную в админке.',
    )

    organization = models.ForeignKey(
        'users.Organization', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices',
        verbose_name='Организация-покупатель',
        help_text='Определяется автоматически по ИНН из счёта.',
    )
    buyer_name = models.CharField('Покупатель (название)', max_length=255, blank=True)
    buyer_inn = models.CharField('Покупатель ИНН', max_length=12, blank=True)
    buyer_kpp = models.CharField('Покупатель КПП', max_length=9, blank=True)

    order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices',
        verbose_name='Заказ',
        help_text='Заполняется вручную или автоматически, если счёт создан на основе заказа.',
    )

    total = models.DecimalField('Итого', max_digits=14, decimal_places=2, default=0)
    vat_total = models.DecimalField('В т.ч. НДС', max_digits=14, decimal_places=2, default=0)

    pdf_file = models.FileField('PDF счёта', upload_to='invoices/%Y/%m/')

    parsed_ok = models.BooleanField('Разобран автоматически', default=False)
    parse_log = models.TextField('Лог разбора', blank=True)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    # ===== ЛОГИСТИКА И ОТГРУЗКА =====
    DELIVERY_STATUS_CHOICES = (
        ('pending', 'Не отгружен'),
        ('partial', 'Отгружен частично'),
        ('shipped', 'Отгружен полностью'),
    )

    delivery_status = models.CharField(
        'Статус отгрузки', max_length=20,
        choices=DELIVERY_STATUS_CHOICES, default='pending'
    )
    delivery_date = models.DateField('Планируемая дата поставки', null=True, blank=True)
    shipment_date = models.DateField('Дата отгрузки', null=True, blank=True)
    manager_comment = models.TextField('Комментарий менеджера', blank=True)

    class Meta:
        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'
        ordering = ('-date', '-id')
        constraints = [
            models.UniqueConstraint(
                fields=('number', 'date'),
                name='unique_invoice_number_date',
            ),
        ]

    def __str__(self):
        date_str = self.date.strftime('%d.%m.%Y') if self.date else 'без даты'
        return f'Счёт №{self.number} от {date_str}'


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE,
        related_name='items', verbose_name='Счёт',
    )
    product = models.ForeignKey(
        'catalog.Product', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoice_items',
        verbose_name='Товар каталога',
        help_text='Определяется автоматически по коду (article) из счёта.',
    )

    row_no = models.PositiveIntegerField('№ строки')
    code = models.CharField('Код / артикул', max_length=100, blank=True)
    name = models.CharField('Наименование', max_length=500)

    quantity = models.DecimalField('Количество', max_digits=12, decimal_places=3)
    price = models.DecimalField('Цена', max_digits=14, decimal_places=2)
    vat_rate = models.DecimalField('Ставка НДС, %', max_digits=5, decimal_places=2)
    vat_amount = models.DecimalField('Сумма НДС', max_digits=14, decimal_places=2)
    amount = models.DecimalField('Сумма', max_digits=14, decimal_places=2)

    shipped_quantity = models.PositiveIntegerField(
        'Отгружено, кол-во', default=0
    )

    shipment_date = models.DateField('Дата отгрузки товара', null=True, blank=True)
    manager_comment = models.CharField(
        'Комментарий (для товара)', max_length=255, blank=True,
        help_text='Например: передано водителю, ожидает сборки'
    )

    @property
    def is_fully_shipped(self):
        return self.shipped_quantity >= self.quantity

    @property
    def is_partially_shipped(self):
        return 0 < self.shipped_quantity < self.quantity

    class Meta:
        verbose_name = 'Позиция счёта'
        verbose_name_plural = 'Позиции счёта'
        ordering = ('row_no',)

    def __str__(self):
        return f'{self.row_no}. {self.name}'