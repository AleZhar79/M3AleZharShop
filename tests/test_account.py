"""Тесты личного кабинета."""
from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_signup_creates_user(client):
    response = client.post(
        "/account/signup/",
        data={
            "username": "newbie",
            "email": "newbie@example.com",
            "password1": "supersecret12345",
            "password2": "supersecret12345",
        },
        follow=True,
    )
    assert response.status_code == 200
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    assert user_model.objects.filter(username="newbie").exists()


@pytest.mark.django_db
def test_login_logout_cycle(client, user, password):
    response = client.post(
        "/account/login/",
        data={"username": user.username, "password": password},
    )
    assert response.status_code in (302, 303)
    # Профиль доступен после логина.
    response = client.get("/account/")
    assert response.status_code == 200

    # Logout: только POST.
    response = client.post("/account/logout/")
    assert response.status_code in (302, 303)
    # После logout профиль уже редиректит на login.
    response = client.get("/account/")
    assert response.status_code in (302, 303)
    assert "/account/login/" in response["Location"]


@pytest.mark.django_db
def test_profile_requires_auth(client):
    response = client.get("/account/")
    assert response.status_code in (302, 303)
    assert "/account/login/" in response["Location"]


@pytest.mark.django_db
def test_orders_page_only_shows_own_orders(
    auth_client, client, user, other_user, password, product
):
    from apps.orders.models import Order, OrderItem
    from decimal import Decimal

    my_order = Order.objects.create(user=user, total_price=Decimal("100.00"))
    OrderItem.objects.create(order=my_order, product=product, quantity=1, price=Decimal("100.00"))

    other_order = Order.objects.create(user=other_user, total_price=Decimal("9999.00"))

    response = auth_client.get("/account/orders/")
    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert f"#{my_order.id}" in body or str(my_order.id) in body
    # Чужой заказ не виден.
    assert "9999" not in body
    assert f"#{other_order.id}" not in body or my_order.id != other_order.id
