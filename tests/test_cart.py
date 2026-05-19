"""Тесты сессионной корзины."""
from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_cart_starts_empty(client):
    response = client.get("/cart/")
    assert response.status_code == 200
    assert "пуста" in response.content.decode("utf-8").lower()


@pytest.mark.django_db
def test_cart_add_then_detail_shows_item(client, product):
    response = client.post(f"/cart/add/{product.id}/", data={"quantity": 2})
    assert response.status_code in (302, 303)

    response = client.get("/cart/")
    body = response.content.decode("utf-8")
    assert product.name in body


@pytest.mark.django_db
def test_cart_update_changes_quantity(client, product):
    client.post(f"/cart/add/{product.id}/", data={"quantity": 1})
    client.post(f"/cart/update/{product.id}/", data={"quantity": 3})
    response = client.get("/cart/")
    body = response.content.decode("utf-8")
    # 3 шт. * 1000.00 = 3000.00 ₽
    assert "3000" in body


@pytest.mark.django_db
def test_cart_remove_clears_item(client, product):
    client.post(f"/cart/add/{product.id}/", data={"quantity": 1})
    client.post(f"/cart/remove/{product.id}/")
    # Смотрим на саму сессию, а не на HTML со всплывающим flash-сообщением.
    cart = client.session.get("cart", {})
    assert str(product.id) not in cart


@pytest.mark.django_db
def test_cart_clear_empties_session(client, product, product_other):
    client.post(f"/cart/add/{product.id}/", data={"quantity": 1})
    client.post(f"/cart/add/{product_other.id}/", data={"quantity": 2})
    client.post("/cart/clear/")
    cart = client.session.get("cart", {})
    assert cart == {}
