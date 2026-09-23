# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from .models import (
    User, Organization, StockNotification,
    PriceRequest, ViewedProduct,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'phone',
        'current_buyer',          # ← новая колонка
        'is_staff', 'is_active',
    )
    search_fields = ('username', 'email', 'phone')
    list_filter = (
        'is_staff', 'is_active', 'is_superuser', 'gender', 'agree_to_terms',
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'gender', 'birth_date', 'middle_name'),
        }),
        ('Согласие', {
            'fields': ('agree_to_terms', 'agreed_at'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'gender', 'birth_date', 'middle_name'),
        }),
    )

    readonly_fields = ('agree_to_terms', 'agreed_at')

    @admin.display(description='Покупает как')
    def current_buyer(self, obj):
        """Показывает, от кого оформляются заказы: от организации или от физлица."""
        org = obj.default_organization
        if org:
            return format_html(
                '<span style="color: #28a745;">🏢 {}</span>',
                org.name
            )
        return format_html(
            '<span style="color: #999;">👤 физлицо</span>'
        )

    def get_queryset(self, request):
        """Оптимизация: подгружаем организации одним запросом."""
        return super().get_queryset(request).prefetch_related('organizations')

    actions = ['block_users', 'unblock_users']

    @admin.action(description='🚫 Заблокировать пользователей')
    def block_users(self, request, queryset):
        """Установить is_active = False."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Заблокировано: {updated} пользователей')

    @admin.action(description='✅ Разблокировать пользователей')
    def unblock_users(self, request, queryset):
        """Установить is_active = True."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Разблокировано: {updated} пользователей')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'inn', 'user', 'is_default', 'created_at')
    list_filter = ('org_type', 'is_default', 'created_at')
    search_fields = ('name', 'inn', 'user__username', 'user__email')
    list_per_page = 20

    fieldsets = (
        ('Основная информация', {
            'fields': ('org_type', 'user', 'name', 'inn', 'kpp', 'ogrn')
        }),
        ('Адреса', {
            'fields': ('address', 'actual_address')
        }),
        ('Контакты', {
            'fields': ('phone', 'email', 'director')
        }),
        ('Банковские реквизиты', {
            'fields': ('bank_name', 'bik', 'account', 'corr_account')
        }),
        ('Настройки', {
            'fields': ('is_default',)
        }),
    )


@admin.register(StockNotification)
class StockNotificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'product_link', 'user', 'created_at', 'notified')
    list_filter = ('notified', 'created_at')
    search_fields = ('email', 'product__name', 'user__username')
    readonly_fields = ('created_at', 'notified_at')
    list_per_page = 50
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ['mark_as_notified']

    @admin.display(description='Товар')
    def product_link(self, obj):
        """Ссылка на товар в админке."""
        url = reverse('admin:catalog_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    @admin.action(description='✅ Отметить как уведомлённые')
    def mark_as_notified(self, request, queryset):
        """Массово отметить подписки как уведомлённые."""
        updated = queryset.update(notified=True, notified_at=timezone.now())
        self.message_user(request, f'Отмечено: {updated} подписок')


@admin.register(PriceRequest)
class PriceRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'short_description', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'email', 'description')
    readonly_fields = ('created_at', 'updated_at', 'user')
    list_per_page = 30
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Контакт', {
            'fields': ('name', 'phone', 'email', 'user')
        }),
        ('Заявка', {
            'fields': ('description', 'comment')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Описание')
    def short_description(self, obj):
        return obj.description[:80] + ('…' if len(obj.description) > 80 else '')


@admin.register(ViewedProduct)
class ViewedProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_link', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'user__email', 'product__name')
    readonly_fields = ('user', 'product', 'viewed_at')
    list_per_page = 50
    date_hierarchy = 'viewed_at'
    ordering = ('-viewed_at',)

    @admin.display(description='Товар')
    def product_link(self, obj):
        """Ссылка на товар в админке."""
        url = reverse('admin:catalog_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    def has_add_permission(self, request):
        """Запрещаем добавлять просмотры вручную."""
        return False