"""Регистрация моделей users в админке."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Админка для кастомной модели User.

    Наследуемся от штатного ``UserAdmin``, чтобы получить готовые формы
    создания/изменения пользователя, фильтры по группам, права и т.д.
    """

    list_display = ("username", "email", "first_name", "last_name", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
