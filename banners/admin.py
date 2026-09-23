# banners/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Banner, BannerPosition


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = (
        'preview', 'title', 'position', 'sort_order',
        'is_active', 'period_display', 'stats_display',
    )
    list_display_links = ('preview', 'title')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('position', 'is_active', 'category')
    search_fields = ('title', 'description', 'link')
    autocomplete_fields = ('category', 'product')

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'description', 'position', 'sort_order', 'is_active'),
        }),
        ('Изображения', {
            'fields': ('image', 'image_mobile'),
        }),
        ('Ссылка', {
            'fields': ('category', 'product', 'link'),
            'description': 'Приоритет: категория → товар → внешняя ссылка',
        }),
        ('Период показа', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',),
        }),
        ('Статистика', {
            'fields': ('views_count', 'clicks_count'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('views_count', 'clicks_count')

    @admin.display(description='Превью')
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:48px;border-radius:4px;">',
                obj.image.url,
            )
        return '—'

    @admin.display(description='Период')
    def period_display(self, obj):
        if not obj.start_date and not obj.end_date:
            return 'всегда'
        start = obj.start_date.strftime('%d.%m.%Y') if obj.start_date else '…'
        end = obj.end_date.strftime('%d.%m.%Y') if obj.end_date else '…'
        return f'{start} — {end}'

    @admin.display(description='Показы / Клики')
    def stats_display(self, obj):
        if not obj.views_count:
            return f'{obj.views_count} / {obj.clicks_count}'
        ctr = obj.clicks_count / obj.views_count * 100
        return f'{obj.views_count} / {obj.clicks_count} ({ctr:.1f}%)'