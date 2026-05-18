"""Конфигурация приложения users."""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Пользователи, регистрация, профили, аутентификация."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"
    verbose_name = "Пользователи"
