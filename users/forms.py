# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import User, Organization, Favorite, StockNotification, PriceRequest


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации с дополнительными полями: email, phone, согласие на ПД."""
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')

    agree_to_terms = forms.BooleanField(
        required=True,
        label='Согласен на обработку персональных данных',
        error_messages={
            'required': 'Необходимо согласие на обработку персональных данных',
        },
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.agree_to_terms = self.cleaned_data['agree_to_terms']
        user.agreed_at = timezone.now()
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Имя',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = (
            'last_name', 'first_name', 'middle_name',
            'gender', 'email', 'phone', 'birth_date',
        )
        widgets = {
            'last_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':       forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'birth_date':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'org_type',
            'name', 'inn', 'kpp', 'ogrn',
            'address', 'actual_address',
            'phone', 'email', 'director',
            'bank_name', 'bik', 'account', 'corr_account',
            'is_default',
        ]
        widgets = {
            'org_type':       forms.Select(attrs={'class': 'form-select'}),
            'name':           forms.TextInput(attrs={'class': 'form-control'}),
            'inn':            forms.TextInput(attrs={'class': 'form-control'}),
            'kpp':            forms.TextInput(attrs={'class': 'form-control'}),
            'ogrn':           forms.TextInput(attrs={'class': 'form-control'}),
            'address':        forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actual_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone':          forms.TextInput(attrs={'class': 'form-control'}),
            'email':          forms.EmailInput(attrs={'class': 'form-control'}),
            'director':       forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name':      forms.TextInput(attrs={'class': 'form-control'}),
            'bik':            forms.TextInput(attrs={'class': 'form-control'}),
            'account':        forms.TextInput(attrs={'class': 'form-control'}),
            'corr_account':   forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        org_type = cleaned.get('org_type')
        inn = (cleaned.get('inn') or '').strip()
        kpp = (cleaned.get('kpp') or '').strip()
        ogrn = (cleaned.get('ogrn') or '').strip()

        if org_type == 'ip':
            if not (inn.isdigit() and len(inn) == 12):
                self.add_error('inn', 'ИНН ИП должен содержать 12 цифр')
            if not (ogrn.isdigit() and len(ogrn) == 15):
                self.add_error('ogrn', 'ОГРНИП должен содержать 15 цифр')
            if kpp:
                self.add_error('kpp', 'У ИП не может быть КПП')

        elif org_type == 'ooo':
            if not (inn.isdigit() and len(inn) == 10):
                self.add_error('inn', 'ИНН ООО должен содержать 10 цифр')
            if not (kpp.isdigit() and len(kpp) == 9):
                self.add_error('kpp', 'КПП ООО должен содержать 9 цифр')
            if not (ogrn.isdigit() and len(ogrn) == 13):
                self.add_error('ogrn', 'ОГРН должен содержать 13 цифр')

        return cleaned


class StockNotificationForm(forms.ModelForm):
    """Форма подписки на уведомление о поступлении."""
    class Meta:
        model = StockNotification
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com',
            }),
        }


class PriceRequestForm(forms.ModelForm):
    """Форма заявки на запрос цены. Для залогиненных — поля скрываются, если есть в профиле."""
    class Meta:
        model = PriceRequest
        fields = ('name', 'phone', 'email', 'description', 'comment')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя',
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
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите, какой товар вам нужен',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Дополнительная информация (необязательно)',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user and user.is_authenticated:
            # Если в профиле есть — скрываем поле
            if user.get_full_name():
                self.fields.pop('name')
            if user.phone:
                self.fields.pop('phone')
            if user.email:
                self.fields.pop('email')