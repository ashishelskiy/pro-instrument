# orders/admin.py
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, DeliveryMethod


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_article', 'price', 'subtotal_display')

    @admin.display(description='Сумма')
    def subtotal_display(self, obj):
        if obj.pk:
            return f'{obj.subtotal} ₽'
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'created_at', 'name', 'phone',
        'buyer_type_display', 'total_price', 'status', 'paid',
    )
    list_editable = ('paid', 'status')
    list_filter = ('status', 'delivery_method', 'payment_method', 'created_at')
    search_fields = ('id', 'name', 'phone', 'email', 'organization__name')
    readonly_fields = ('created_at', 'updated_at', 'delivery_method_name')
    list_per_page = 30
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [OrderItemInline]

    fieldsets = (
        ('Кто заказал', {
            'fields': ('user', 'organization')
        }),
        ('Контакт', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Доставка', {
            'fields': ('delivery_method', 'delivery_method_name', 'delivery_price', 'address')
        }),
        ('Оплата', {
            'fields': ('payment_method', 'paid')
        }),
        ('Дополнительно', {
            'fields': ('comment',)
        }),
        ('Статус и итоги', {
            'fields': ('status', 'total_price')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Покупает как')
    def buyer_type_display(self, obj):
        if obj.organization:
            return format_html(
                '<span style="color: #28a745;">🏢 {}</span>',
                obj.organization.name
            )
        return format_html('<span style="color: #999;">👤 физлицо</span>')


    def save_model(self, request, obj, form, change):
        # Пересчитываем итоговую сумму
        if obj.pk:
            # Если заказ уже есть, берем сумму товаров из связанных позиций
            items_total = sum(item.price * item.quantity for item in obj.items.all())
            obj.total_price = items_total + obj.delivery_price
        else:
            # Если это новый заказ (создается в админке), то total_price = delivery_price
            # (товары добавляются через inline, но они сохраняются после этого метода, так что для новых заказов в админке это не сработает идеально, но для существующих — да)
            obj.total_price = obj.delivery_price

        old_status = None
        if change:
            try:
                old_status = Order.objects.get(pk=obj.pk).status
            except Order.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

        # Если статус изменился — письмо клиенту
        if old_status and old_status != obj.status and obj.email:
            try:
                send_mail(
                    subject=f'Статус заказа №{obj.pk} изменён',
                    message=(
                        f'Здравствуйте, {obj.name}!\n\n'
                        f'Статус вашего заказа №{obj.pk} изменён.\n\n'
                        f'Новый статус: {obj.get_status_display()}\n\n'
                        f'С уважением,\n'
                        f'команда PRO-инструмент'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[obj.email],
                    fail_silently=True,
                )
            except Exception:
                pass


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('price', 'is_active', 'sort_order')
    ordering = ('sort_order', 'name')