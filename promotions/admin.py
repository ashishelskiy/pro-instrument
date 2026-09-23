from django.contrib import admin
from .models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'sort_order', 'created_at')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'sort_order')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories', 'products')
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'description', 'image', 'is_active', 'sort_order')
        }),
        ('Товары', {
            'fields': ('categories', 'products'),
            'description': 'Выберите категории и/или отдельные товары для акции'
        }),
    )