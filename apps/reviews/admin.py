"""Регистрация моделей reviews в админке."""

from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Админка отзывов."""

    list_display = ("id", "product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = (
        "product__name",
        "user__username",
        "user__email",
        "comment",
    )
    autocomplete_fields = ("product", "user")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    list_select_related = ("product", "user")
    date_hierarchy = "created_at"
