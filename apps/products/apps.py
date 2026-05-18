"""Конфигурация приложения products."""
from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """Каталог: категории и товары."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"
    label = "products"
    verbose_name = "Товары и категории"
