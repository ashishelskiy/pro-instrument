# orders/forms.py
from django import forms
from .models import Order, DeliveryMethod


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            'name', 'phone', 'email',
            'delivery_method', 'address',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Только активные способы доставки
        delivery_field = self.fields['delivery_method']
        delivery_field.queryset = DeliveryMethod.objects.filter(is_active=True)
        delivery_field.empty_label = None

        # Красивое отображение: «Курьером — 500 ₽»
        def delivery_label(obj):
            if obj.price and obj.price > 0:
                return f'{obj.name} — {obj.price:.2f} ₽'
            return f'{obj.name} — бесплатно'

        delivery_field.label_from_instance = delivery_label

    def clean(self):
        cleaned = super().clean()
        delivery = cleaned.get('delivery_method')
        address = (cleaned.get('address') or '').strip()

        # Если не самовывоз — адрес обязателен
        if delivery and delivery.name.lower() != 'самовывоз' and not address:
            self.add_error('address', 'Укажите адрес доставки')

        return cleaned