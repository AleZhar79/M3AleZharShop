"""Бизнес-логика приложения orders."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.urls import reverse

from apps.cart.cart import Cart
from apps.products.models import Product

from .models import Order, OrderItem


class EmptyCartError(Exception):
    """Попытка оформить пустую корзину."""


class OutOfStockError(Exception):
    """Запрошено больше, чем есть на складе."""

    def __init__(self, product: Product, requested: int, available: int) -> None:
        super().__init__(f"«{product.name}»: запрошено {requested}, доступно {available}.")
        self.product = product
        self.requested = requested
        self.available = available


@transaction.atomic
def place_order(*, user, cart: Cart, form_data: dict) -> Order:
    """Создать заказ из корзины.

    Шаги (в транзакции):
      1. Блокируем строки товаров `SELECT ... FOR UPDATE`.
      2. Проверяем остатки. Если чего-то не хватает — raise OutOfStockError
         и транзакция откатывается.
      3. Создаём Order и OrderItem'ы (цена-снимок берётся из корзины).
      4. Списываем остатки атомарно через F-выражения.
      5. Чистим сессионную корзину.
    """
    if cart.is_empty:
        raise EmptyCartError("Корзина пуста.")

    # Снимок позиций корзины + блокировка товаров
    items_snapshot = list(cart)
    product_ids = [it["product"].pk for it in items_snapshot]
    locked = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=product_ids)}

    for it in items_snapshot:
        p = locked.get(it["product"].pk)
        if p is None or not p.is_active:
            raise OutOfStockError(it["product"], it["quantity"], 0)
        if p.stock < it["quantity"]:
            raise OutOfStockError(p, it["quantity"], p.stock)

    # Создаём заказ
    order = Order.objects.create(
        user=user,
        customer_name=form_data["customer_name"],
        contact_email=form_data["contact_email"],
        contact_phone=form_data["contact_phone"],
        shipping_address=form_data["shipping_address"],
        comment=form_data.get("comment", ""),
        total_price=Decimal("0.00"),
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=it["product"],
                quantity=it["quantity"],
                price=it["price"],
            )
            for it in items_snapshot
        ]
    )

    # Списываем остатки одним UPDATE на каждый товар (атомарно через F).
    for it in items_snapshot:
        Product.objects.filter(pk=it["product"].pk).update(stock=F("stock") - it["quantity"])

    # Пересчитываем total из реально сохранённых OrderItem'ов.
    order.recalculate_total()
    order.save(update_fields=["total_price", "updated_at"])

    cart.clear()
    return order


def send_order_confirmation(order: Order, request=None) -> None:
    """Отправить письма клиенту и админу. Падать при ошибках email не должно —
    оборачиваем в try/except и пишем в logging; в учебном проекте достаточно
    тихого fail_silently=True у send_mail."""
    items = list(order.items.select_related("product"))
    admin_url_path = reverse("admin:orders_order_change", args=[order.pk])
    base_url = ""
    if request is not None:
        base_url = f"{request.scheme}://{request.get_host()}"

    context = {
        "order": order,
        "items": items,
        "admin_url": f"{base_url}{admin_url_path}" if base_url else admin_url_path,
    }
    subject_client = f"Заказ #{order.pk} принят — M3AleZharShop"
    body_client = render_to_string("orders/email/order_created_client.txt", context)

    subject_admin = f"Новый заказ #{order.pk}"
    body_admin = render_to_string("orders/email/order_created_admin.txt", context)

    recipients_client = [order.contact_email] if order.contact_email else []
    admins = getattr(settings, "ORDER_NOTIFICATIONS_TO", None) or [
        a[1] for a in getattr(settings, "ADMINS", [])
    ]

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@m3alezharshop.local")

    if recipients_client:
        send_mail(subject_client, body_client, from_email, recipients_client, fail_silently=True)
    if admins:
        send_mail(subject_admin, body_admin, from_email, admins, fail_silently=True)
