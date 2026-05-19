"""Настройки для запуска тестов: SQLite в памяти + console email.

Использовать через ``DJANGO_SETTINGS_MODULE=config.test_settings``.
"""

from __future__ import annotations

from config.settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Локмем — чтобы можно было проверять mail.outbox в тестах.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Шире чем localhost — тестовый клиент использует "testserver".
ALLOWED_HOSTS = ["*"]

# Быстрее хешируем пароли в тестах.
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
