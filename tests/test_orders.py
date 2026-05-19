"""Тесты сервисного слоя orders.place_order."""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.core import mail

from apps.cart.cart import Cart
from apps.orders.models import Order, OrderStatus
from apps.orders.services import (
    EmptyCartError,
    OutOfStockError,
    place_order,
    send_order_confirmation,
)


@pytest.fixture
def request_with_session(rf):
    """Подготовленный HttpRequest с активной сессией — нужен Cart."""
    request = rf.get("/")
    # SessionMiddleware ещё не вызывался — даём пустую сессию вручную.
    from django.contrib.sessions.backends.db import SessionStore

    request.session = SessionStore()
    return request


@pytest.fixture
def order_form_data():
    return {
        "customer_name": "Иван Иванов",
        "contact_email": "buyer@example.com",
        "contact_phone": "+79990000000",
        "shipping_address": "Москва, Тверская, 1",
        "comment": "Звоните перед доставкой",
    }


@pytest.mark.django_db
def test_place_order_creates_order_and_decrements_stock(
    request_with_session, user, product, product_other, order_form_data
):
    cart = Cart(request_with_session)
    cart.add(product, quantity=2)
    cart.add(product_other, quantity=3)

    order = place_order(user=user, cart=cart, form_data=order_form_data)

    assert order.pk is not None
    assert order.status == OrderStatus.PENDING
    # 2 * 1000 + 3 * 150 = 2450
    assert order.total_price == Decimal("2450.00")
    assert order.items.count() == 2

    product.refresh_from_db()
    product_other.refresh_from_db()
    assert product.stock == 10 - 2
    assert product_other.stock == 20 - 3


@pytest.mark.django_db
def test_place_order_empty_cart_raises(
    request_with_session, user, order_form_data
):
    cart = Cart(request_with_session)
    with pytest.raises(EmptyCartError):
        place_order(user=user, cart=cart, form_data=order_form_data)


@pytest.mark.django_db
def test_place_order_out_of_stock_rolls_back(
    request_with_session, user, product, order_form_data
):
    cart = Cart(request_with_session)
    cart.add(product, quantity=product.stock)  # ровно stock
    # Искусственно портим состояние: снижаем stock ниже того, что
    # уже лежит в корзине — классическая race condition, которую и должен
    # ловить place_order().
    product.stock = 1
    product.save(update_fields=("stock",))

    with pytest.raises(OutOfStockError):
        place_order(user=user, cart=cart, form_data=order_form_data)

    # Заказа быть не должно, остаток не тронут (остался 1).
    assert Order.objects.count() == 0
    product.refresh_from_db()
    assert product.stock == 1


@pytest.mark.django_db
def test_send_order_confirmation_sends_email(
    request_with_session, user, product, order_form_data
):
    cart = Cart(request_with_session)
    cart.add(product, quantity=1)
    order = place_order(user=user, cart=cart, form_data=order_form_data)

    mail.outbox.clear()
    send_order_confirmation(order)

    # Минимум одно письмо клиенту; копии админам — опционально.
    assert len(mail.outbox) >= 1
    recipients = {addr for msg in mail.outbox for addr in msg.to}
    assert order_form_data["contact_email"] in recipients
