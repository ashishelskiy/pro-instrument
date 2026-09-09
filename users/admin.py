# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


# Регистрируем кастомную модель пользователя в админке
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Настройка отображения кастомных пользователей в админке
    """
    # Поля, которые показываем в списке пользователей
    list_display = ('username', 'email', 'phone', 'is_staff', 'is_active')

    # Поля для поиска
    search_fields = ('username', 'email', 'phone')

    # Фильтры в правой колонке
    list_filter = ('is_staff', 'is_active', 'is_superuser')

    # Добавляем телефон и аватар в форму редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'avatar'),
        }),
    )