"""Конфигурация приложения reviews."""
from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """Отзывы на товары."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reviews"
    label = "reviews"
    verbose_name = "Отзывы"
