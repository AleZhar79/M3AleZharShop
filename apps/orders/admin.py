"""Регистрация моделей orders в админке."""
from django.contrib import admin

from apps.orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Позиции заказа прямо на странице заказа."""

    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("line_total",)
    fields = ("product", "quantity", "price", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка заказов."""

    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email", "contact_email")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "total_price")
    inlines = (OrderItemInline,)
    ordering = ("-created_at",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Отдельная админка позиций — удобно для поиска и аналитики."""

    list_display = ("id", "order", "product", "quantity", "price", "line_total")
    list_filter = ("order__status",)
    search_fields = ("order__id", "product__name")
    autocomplete_fields = ("order", "product")
