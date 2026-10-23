# orders/forms.py
from django import forms
from .models import Order, DeliveryMethod


class OrderForm(forms.ModelForm):
    city = forms.CharField(
        label='Город',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Начните вводить город',
            'autocomplete': 'off',
            'id': 'id_city',
        })
    )
    # Заменяем автоматическое поле на ChoiceField
    delivery_method = forms.ChoiceField(
        label='Способ доставки',
        widget=forms.RadioSelect(),
        required=False,
    )
    class Meta:
        model = Order
        fields = (
            'name', 'phone', 'email',
            'city',
            # 'delivery_method', 'address',
            'payment_method',
            'comment',
        )
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ФИО',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'tel',
                'placeholder': '+7 (___) ___-__-__',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com',
            }),
            'delivery_method': forms.RadioSelect(),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Город, улица, дом, квартира',
            }),
            'payment_method': forms.RadioSelect(),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Комментарий к заказу (необязательно)',
            }),
        }
        labels = {
            'name': 'ФИО',
            'phone': 'Телефон',
            'email': 'Email',
            'delivery_method': 'Способ доставки',
            'address': 'Адрес доставки',
            'payment_method': 'Способ оплаты',
            'comment': 'Комментарий',
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #
    #     # Только активные способы доставки
    #     delivery_field = self.fields['delivery_method']
    #     delivery_field.queryset = DeliveryMethod.objects.filter(is_active=True)
    #     delivery_field.empty_label = None
    #
    #     # Красивое отображение: «Курьером — 500 ₽»
    #     def delivery_label(obj):
    #         if obj.price and obj.price > 0:
    #             return f'{obj.name} — {obj.price:.2f} ₽'
    #         return f'{obj.name} — бесплатно'
    #
    #     delivery_field.label_from_instance = delivery_label
    #
    #     # По умолчанию — самовывоз (если форма не связана с данными и поле ещё не выбрано)
    #     if not self.is_bound and not self.instance.pk:
    #         default_delivery = DeliveryMethod.objects.filter(
    #             name__iexact='Самовывоз',
    #             is_active=True
    #         ).first()
    #         if default_delivery:
    #             delivery_field.initial = default_delivery.pk

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Заполняем choices из базы (самовывоз и другие способы)
        delivery_field = self.fields['delivery_method']
        choices = []
        for d in DeliveryMethod.objects.filter(is_active=True):
            if d.price and d.price > 0:
                label = f'{d.name} — {d.price:.2f} ₽'
            else:
                label = f'{d.name} — бесплатно'
            choices.append((str(d.pk), label))
        delivery_field.choices = choices

        # ДОБАВЛЯЕМ СДЭК В ВАРИАНТЫ, чтобы форма проходила валидацию
        choices.append(('cdek', 'СДЭК (пункт выдачи)'))
        delivery_field.choices = choices

        # По умолчанию — самовывоз
        if not self.is_bound and not self.instance.pk:
            default_delivery = DeliveryMethod.objects.filter(
                name__iexact='Самовывоз', is_active=True
            ).first()
            if default_delivery:
                delivery_field.initial = str(default_delivery.pk)

    # def clean(self):
    #     cleaned = super().clean()
    #     delivery = cleaned.get('delivery_method')
    #     address = (cleaned.get('address') or '').strip()
    #
    #     # Если не самовывоз — адрес обязателен
    #     if delivery and delivery.name.lower() != 'самовывоз' and not address:
    #         self.add_error('address', 'Укажите адрес доставки')
    #
    #     return cleaned

    # def clean(self):
    #     cleaned = super().clean()
    #     delivery_id = cleaned.get('delivery_method')
    #     address = (cleaned.get('address') or '').strip()
    #
    #     # Если выбран не самовывоз — адрес обязателен
    #     if delivery_id:
    #         try:
    #             delivery = DeliveryMethod.objects.get(pk=delivery_id)
    #             if delivery.name.lower() != 'самовывоз' and not address:
    #                 self.add_error('address', 'Укажите адрес доставки')
    #         except (DeliveryMethod.DoesNotExist, ValueError):
    #             # Это id тарифа СДЭК (например, "136") — адрес тоже нужен
    #             if not address:
    #                 self.add_error('address', 'Укажите адрес доставки')
    #
    #     return cleaned
    # def clean(self):
    #     cleaned = super().clean()
    #     delivery_id = cleaned.get('delivery_method')
    #     address = (cleaned.get('address') or '').strip()
    #     cdek_pvz_code = (self.data.get('cdek_pvz_code') or '').strip()
    #
    #     if delivery_id:
    #         try:
    #             delivery = DeliveryMethod.objects.get(pk=delivery_id)
    #             is_pickup = delivery.name.lower() == 'самовывоз'
    #         except (DeliveryMethod.DoesNotExist, ValueError):
    #             delivery = None
    #             is_pickup = False  # это тариф СДЭК
    #
    #         # Для доставки (не самовывоза из базы) — адрес обязателен
    #         if not is_pickup and not address:
    #             self.add_error('address', 'Укажите адрес доставки')
    #
    #         # Для СДЭК — обязателен выбранный ПВЗ
    #         if not is_pickup and delivery is None and not cdek_pvz_code:
    #             self.add_error(None, 'Выберите пункт выдачи СДЭК')
    #
    #     return cleaned
    def clean(self):
        cleaned = super().clean()
        delivery_id = self.data.get('delivery_method') # Берем из data
        address = (cleaned.get('address') or '').strip()
        cdek_pvz_code = (self.data.get('cdek_pvz_code') or '').strip()

        if delivery_id == 'cdek':
            if not cdek_pvz_code:
                self.add_error(None, 'Выберите пункт выдачи СДЭК')
        elif delivery_id:
            # Это ID из базы (самовывоз)
            try:
                delivery = DeliveryMethod.objects.get(pk=delivery_id)
                if delivery.name.lower() != 'самовывоз' and not address:
                    self.add_error('address', 'Укажите адрес доставки')
            except (DeliveryMethod.DoesNotExist, ValueError):
                pass

        return cleaned