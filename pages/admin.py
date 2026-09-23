# pages/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Page, News, SiteSettings


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'updated_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_per_page = 20

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'is_published')
        }),
        ('Содержимое', {
            'fields': ('content',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
    )


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published', 'image_preview')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_per_page = 20
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'is_published', 'published_at')
        }),
        ('Контент', {
            'fields': ('short_description', 'content', 'image')
        }),
    )

    @admin.display(description='Превью')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 40px; border-radius: 4px;">',
                obj.image.url
            )
        return '—'


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Настройки сайта — только одна запись."""
    fieldsets = (
        ('Основное', {
            'fields': ('site_name', 'site_description', 'logo')
        }),
        ('Контакты', {
            'fields': ('phone', 'email', 'admin_email', 'address', 'work_hours')
        }),
        ('Реквизиты', {
            'fields': ('company_name', 'inn', 'ogrn', 'kpp'),
            'classes': ('collapse',),
        }),
        ('Соцсети', {
            'fields': ('vk_url', 'telegram_url', 'whatsapp_url'),
            'classes': ('collapse',),
        }),
        ('Служебное', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        """Запрещаем создавать больше одной записи."""
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удалять."""
        return False