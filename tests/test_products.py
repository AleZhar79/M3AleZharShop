"""Тесты каталога: список товаров, фильтры, поиск, пагинация, деталь."""
from __future__ import annotations

from decimal import Decimal

import pytest

from apps.products.models import Product


@pytest.mark.django_db
def test_product_list_shows_only_active(client, product, inactive_product):
    response = client.get("/products/")
    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert product.name in body
    assert inactive_product.name not in body


@pytest.mark.django_db
def test_product_detail_returns_200(client, product):
    response = client.get(f"/products/product/{product.slug}/")
    assert response.status_code == 200
    assert product.name in response.content.decode("utf-8")


@pytest.mark.django_db
def test_product_detail_404_for_inactive(client, inactive_product):
    response = client.get(f"/products/product/{inactive_product.slug}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_product_search_finds_by_name(client, product, product_other):
    # SQLite не умеет case-insensitive LIKE для кириллицы без ICU,
    # поэтому ищем по латинской части имени.
    response = client.get("/products/?q=Кабель")
    body = response.content.decode("utf-8")
    assert product_other.name in body
    assert product.name not in body


@pytest.mark.django_db
def test_product_price_filter(client, category):
    Product.objects.create(
        name="Дешёвый",
        slug="cheap",
        price=Decimal("10.00"),
        category=category,
        stock=1,
    )
    Product.objects.create(
        name="Дорогой",
        slug="expensive",
        price=Decimal("5000.00"),
        category=category,
        stock=1,
    )
    response = client.get("/products/?price_min=1000")
    body = response.content.decode("utf-8")
    assert "Дорогой" in body
    assert "Дешёвый" not in body
