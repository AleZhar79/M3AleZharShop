"""Конфигурация приложения orders."""
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """Заказы и корзина."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"
    label = "orders"
    verbose_name = "Заказы"
