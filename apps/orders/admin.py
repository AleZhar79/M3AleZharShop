"""Регистрация моделей orders в админке."""
from django.contrib import admin, messages

from apps.orders.models import Order, OrderItem, OrderStatus


class OrderItemInline(admin.TabularInline):
    """Позиции заказа прямо на странице заказа."""

    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("line_total",)
    fields = ("product", "quantity", "price", "line_total")


@admin.action(description="Отметить как оплаченные")
def mark_as_paid(modeladmin, request, queryset):
    updated = queryset.update(status=OrderStatus.PAID)
    messages.success(request, f"Обновлено заказов: {updated}.")


@admin.action(description="Отметить как отправленные")
def mark_as_shipped(modeladmin, request, queryset):
    updated = queryset.update(status=OrderStatus.SHIPPED)
    messages.success(request, f"Обновлено заказов: {updated}.")


@admin.action(description="Отметить как доставленные")
def mark_as_delivered(modeladmin, request, queryset):
    updated = queryset.update(status=OrderStatus.DELIVERED)
    messages.success(request, f"Обновлено заказов: {updated}.")


@admin.action(description="Отменить заказы")
def mark_as_cancelled(modeladmin, request, queryset):
    updated = queryset.update(status=OrderStatus.CANCELLED)
    messages.warning(request, f"Отменено заказов: {updated}.")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка заказов."""

    list_display = (
        "id",
        "user",
        "status",
        "customer_name",
        "contact_phone",
        "total_price",
        "created_at",
    )
    list_filter = ("status", "created_at")
    list_select_related = ("user",)
    search_fields = (
        "id", "user__username", "user__email",
        "contact_email", "contact_phone", "customer_name",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "total_price")
    inlines = (OrderItemInline,)
    ordering = ("-created_at",)
    actions = (mark_as_paid, mark_as_shipped, mark_as_delivered, mark_as_cancelled)
    date_hierarchy = "created_at"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Отдельная админка позиций — удобно для поиска и аналитики."""

    list_display = ("id", "order", "product", "quantity", "price", "line_total")
    list_filter = ("order__status",)
    search_fields = ("order__id", "product__name")
    autocomplete_fields = ("order", "product")
