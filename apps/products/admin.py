"""Регистрация моделей products в админке."""
from django.contrib import admin

from apps.products.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка категорий."""

    list_display = ("name", "slug", "parent", "created_at")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("parent",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка товаров."""

    list_display = ("name", "category", "price", "stock", "is_active", "created_at")
    list_filter = ("is_active", "category", "created_at")
    list_editable = ("price", "stock", "is_active")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
