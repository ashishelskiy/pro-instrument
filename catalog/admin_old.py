from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Category, Brand, Product, ProductImage,
    ProductProperty, CategoryProperty
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_main', 'order')
    ordering = ('order',)


class ProductPropertyInline(admin.TabularInline):
    model = ProductProperty
    extra = 1
    fields = ('name', 'value')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'article', 'price', 'in_stock', 'brand', 'category')
    list_filter = ('in_stock', 'brand', 'category')
    search_fields = ('id', 'name', 'article', 'url')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductImageInline, ProductPropertyInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'name', 'slug', 'article', 'url', 'price', 'old_price',
                      'in_stock', 'image', 'brand', 'category')
        }),
        ('Описание', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductProperty)
class ProductPropertyAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value')
    list_filter = ('name',)
    search_fields = ('product__name', 'name', 'value')


@admin.register(CategoryProperty)
class CategoryPropertyAdmin(admin.ModelAdmin):
    list_display = ('category', 'name', 'is_required', 'sort_order')
    list_filter = ('category', 'is_required')
    search_fields = ('name',)