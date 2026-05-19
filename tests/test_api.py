"""Тесты REST API (auth, products, orders)."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest


def _json_post(client, url, payload, **extra):
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
        **extra,
    )


@pytest.mark.django_db
def test_auth_me_requires_token(client):
    response = client.get("/api/auth/me/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_register_then_obtain_jwt(client):
    response = _json_post(
        client,
        "/api/auth/register/",
        {
            "username": "apiuser",
            "email": "apiuser@example.com",
            "password": "supersecret12345",
        },
    )
    assert response.status_code == 201
    response = _json_post(
        client,
        "/api/auth/token/",
        {"username": "apiuser", "password": "supersecret12345"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access" in body and "refresh" in body


@pytest.mark.django_db
def test_products_list_paginated_and_filterable(client, product, product_other, inactive_product):
    response = client.get("/api/products/")
    assert response.status_code == 200
    body = response.json()
    # inactive_product не попадает в выдачу
    assert body["count"] == 2
    slugs = {row["slug"] for row in body["results"]}
    assert slugs == {product.slug, product_other.slug}

    # Фильтр по min_price отрезает дешёвый товар.
    response = client.get("/api/products/?min_price=500")
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["slug"] == product.slug


@pytest.mark.django_db
def test_create_order_via_api(client, user, password, product, product_other):
    response = _json_post(
        client,
        "/api/auth/token/",
        {"username": user.username, "password": password},
    )
    access = response.json()["access"]

    payload = {
        "customer_name": "Иван",
        "shipping_address": "СПб, Невский 1",
        "contact_phone": "+79990000000",
        "contact_email": "buyer@example.com",
        "items": [
            {"product": product.id, "quantity": 2},
            {"product": product_other.id, "quantity": 3},
        ],
    }
    response = _json_post(
        client,
        "/api/orders/",
        payload,
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert Decimal(body["total_price"]) == Decimal("2450.00")
    assert body["status"] == "pending"
    assert len(body["items"]) == 2

    product.refresh_from_db()
    product_other.refresh_from_db()
    assert product.stock == 8
    assert product_other.stock == 17


@pytest.mark.django_db
def test_swagger_and_schema_endpoints(client):
    response = client.get("/api/schema/")
    assert response.status_code == 200
    response = client.get("/api/docs/")
    assert response.status_code == 200
