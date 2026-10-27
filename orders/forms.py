# orders/forms.py
from django import forms
from .models import Order, DeliveryMethod


class OrderForm(forms.ModelForm):
    city = forms.CharField(
        label='Город',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Начните вводить город',
            'autocomplete': 'off',
            'id': 'id_city',
        })
    )

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
            'address',
            'payment_method',
            'comment',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО'}),
            'phone': forms.TextInput(
                attrs={'class': 'form-control', 'type': 'tel', 'placeholder': '+7 (___) ___-__-__'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'address': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Город, улица, дом, квартира'}),
            'payment_method': forms.RadioSelect(),
            'comment': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Комментарий к заказу (необязательно)'}),
        }
        labels = {
            'name': 'ФИО',
            'phone': 'Телефон',
            'email': 'Email',
            'address': 'Адрес доставки',
            'payment_method': 'Способ оплаты',
            'comment': 'Комментарий',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Формируем варианты для способов доставки
        delivery_field = self.fields['delivery_method']
        choices = []
        for d in DeliveryMethod.objects.filter(is_active=True):
            if d.price and d.price > 0:
                label = f'{d.name} — {d.price:.2f} ₽'
            elif d.description:
                label = f'{d.name} — {d.description}'
            else:
                label = f'{d.name} — бесплатно'
            choices.append((str(d.pk), label))

        # СДЭК добавляем вручную, так как его нет в базе (или он там есть, но нам нужна особая логика)
        # choices.append(('cdek', 'СДЭК (пункт выдачи)'))
        delivery_field.choices = choices

        # Если форма не связана с данными, выбираем Самовывоз по умолчанию
        if not self.is_bound and not self.instance.pk:
            default = DeliveryMethod.objects.filter(name__iexact='Самовывоз', is_active=True).first()
            if default:
                delivery_field.initial = str(default.pk)

    # def clean(self):
    #     cleaned = super().clean()
    #     delivery_id = self.data.get('delivery_method')
    #     city = (cleaned.get('city') or '').strip()
    #     address = (cleaned.get('address') or '').strip()
    #     cdek_pvz_code = (self.data.get('cdek_pvz_code') or '').strip()
    #
    #     if delivery_id == 'cdek':
    #         if not city:
    #             self.add_error('city', 'Укажите город для расчета СДЭК')
    #         if not cdek_pvz_code:
    #             self.add_error(None, 'Выберите пункт выдачи СДЭК')
    #     elif delivery_id:
    #         try:
    #             delivery = DeliveryMethod.objects.get(pk=delivery_id)
    #             if delivery.name.lower() != 'самовывоз' and not address:
    #                 self.add_error('address', 'Укажите адрес доставки')
    #         except (DeliveryMethod.DoesNotExist, ValueError):
    #             pass
    #
    #     return cleaned

    def clean(self):
        cleaned = super().clean()
        delivery_id = self.data.get('delivery_method')
        payment_method = cleaned.get('payment_method')
        city = (cleaned.get('city') or '').strip()
        address = (cleaned.get('address') or '').strip()
        cdek_pvz_code = (self.data.get('cdek_pvz_code') or '').strip()

        if delivery_id:
            try:
                delivery = DeliveryMethod.objects.get(pk=delivery_id)
                is_cdek = 'сдэк' in delivery.name.lower() or 'cdek' in delivery.name.lower()
                is_pickup = 'самовывоз' in delivery.name.lower()

                if is_cdek:
                    if not city:
                        self.add_error('city', 'Укажите город для расчета СДЭК')
                    if not cdek_pvz_code:
                        self.add_error(None, 'Выберите пункт выдачи СДЭК')
                    if payment_method == 'cash':
                        self.add_error('payment_method', 'Для доставки СДЭК доступна только онлайн-оплата картой')
                elif not is_pickup and not address:
                    self.add_error('address', 'Укажите адрес доставки')
            except (DeliveryMethod.DoesNotExist, ValueError):
                pass

        return cleaned