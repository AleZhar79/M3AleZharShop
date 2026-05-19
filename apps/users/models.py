"""Модели приложения users."""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Кастомная модель пользователя.

    Наследует все стандартные поля Django (username, email, password, ...),
    что позволяет легко расширять профиль в будущем (телефон, аватар,
    предпочтения и т.п.) без болезненных миграций.

    На этом шаге дополнительные поля не добавляются — главное закрепить
    собственную модель как ``AUTH_USER_MODEL`` до первой миграции
    приложений проекта.
    """

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("-date_joined",)

    def __str__(self) -> str:
        return self.get_username()
