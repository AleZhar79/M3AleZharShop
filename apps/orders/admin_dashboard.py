"""Аналитическая dashboard-страница для админки.

Регистрируется как кастомный URL ``admin/dashboard/``. Доступ только для
``staff``. Считает основные KPI магазина: выручка, заказы по статусам,
топ товаров, продажи по дням за выбранный период.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.orders.models import Order, OrderItem, OrderStatus
from apps.products.models import Product
from apps.reviews.models import Review

PAID_STATUSES = (
    OrderStatus.PAID,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
)


@staff_member_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Сводка по магазину.

    Период выбирается через ``?days=7|30|90`` (по умолчанию 30).
    Для выручки учитываются только статусы, считающиеся «оплаченными».
    """
    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    days = max(1, min(days, 365))
    since = timezone.now() - timedelta(days=days)

    # Общие KPI ----------------------------------------------------------
    orders_qs = Order.objects.filter(created_at__gte=since)

    total_orders = orders_qs.count()
    paid_qs = orders_qs.filter(status__in=PAID_STATUSES)
    revenue = paid_qs.aggregate(
        total=Coalesce(
            Sum("total_price"),
            Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
    )["total"]
    avg_order = (revenue / paid_qs.count()) if paid_qs.exists() else Decimal("0.00")

    # Заказы по статусам -------------------------------------------------
    by_status = orders_qs.values("status").annotate(n=Count("id")).order_by("-n")
    status_display = dict(OrderStatus.choices)
    by_status_rows = [
        {"status": status_display.get(row["status"], row["status"]), "n": row["n"]}
        for row in by_status
    ]

    # Топ-10 товаров по выручке -----------------------------------------
    line_total_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    # ВАЖНО: аннотации называем НЕ так же, как поля модели, иначе F('quantity')
    # в следующих аннотациях будет интерпретирован как ссылка на агрегат.
    top_products = (
        OrderItem.objects.filter(order__in=paid_qs)
        .values("product__id", "product__name")
        .annotate(
            total_qty=Coalesce(Sum("quantity"), Value(0)),
            revenue=Coalesce(
                Sum(line_total_expr),
                Value(
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            ),
        )
        .order_by("-revenue")[:10]
    )

    # Продажи по дням ---------------------------------------------------
    daily = (
        paid_qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            orders=Count("id"),
            revenue=Coalesce(
                Sum("total_price"),
                Value(
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            ),
        )
        .order_by("day")
    )

    # Низкие остатки и общая статистика каталога ------------------------
    low_stock = Product.objects.filter(is_active=True, stock__lte=5, stock__gt=0).order_by("stock")[
        :10
    ]
    out_of_stock_count = Product.objects.filter(is_active=True, stock=0).count()
    catalog_total = Product.objects.filter(is_active=True).count()
    reviews_total = Review.objects.count()

    context = {
        **admin.site.each_context(request),
        "title": "Аналитика магазина",
        "days": days,
        "since": since,
        "total_orders": total_orders,
        "paid_orders": paid_qs.count(),
        "revenue": revenue,
        "avg_order": avg_order,
        "by_status_rows": by_status_rows,
        "top_products": list(top_products),
        "daily": list(daily),
        "low_stock": low_stock,
        "out_of_stock_count": out_of_stock_count,
        "catalog_total": catalog_total,
        "reviews_total": reviews_total,
        "period_choices": (7, 30, 90, 180, 365),
    }
    return render(request, "admin/dashboard.html", context)
