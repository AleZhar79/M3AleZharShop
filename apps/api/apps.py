"""Конфигурация приложения REST API."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """REST API поверх существующих доменных приложений."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api"
    verbose_name = "REST API"
