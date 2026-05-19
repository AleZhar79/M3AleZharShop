"""Общие фикстуры pytest для всех тестов проекта."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.products.models import Category, Product

User = get_user_model()


@pytest.fixture
def password() -> str:
    return "testpass12345"


@pytest.fixture
def user(db, password):
    """Обычный покупатель."""
    return User.objects.create_user(
        username="buyer",
        email="buyer@example.com",
        password=password,
        first_name="Иван",
    )


@pytest.fixture
def other_user(db, password):
    """Второй пользователь — для проверок изоляции данных."""
    return User.objects.create_user(
        username="other",
        email="other@example.com",
        password=password,
    )


@pytest.fixture
def staff_user(db, password):
    return User.objects.create_user(
        username="manager",
        email="manager@example.com",
        password=password,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(name="Электроника", slug="elektronika")


@pytest.fixture
def product(category) -> Product:
    return Product.objects.create(
        name="Смартфон Test",
        slug="smartfon-test",
        description="Описание смартфона.",
        price=Decimal("1000.00"),
        category=category,
        stock=10,
        is_active=True,
    )


@pytest.fixture
def product_other(category) -> Product:
    return Product.objects.create(
        name="Кабель Test",
        slug="kabel-test",
        description="Описание кабеля.",
        price=Decimal("150.00"),
        category=category,
        stock=20,
        is_active=True,
    )


@pytest.fixture
def inactive_product(category) -> Product:
    return Product.objects.create(
        name="Скрытый",
        slug="hidden",
        price=Decimal("99.00"),
        category=category,
        stock=5,
        is_active=False,
    )


@pytest.fixture
def auth_client(client, user, password):
    """Залогиненный обычным сессионным логином клиент."""
    client.login(username=user.username, password=password)
    return client


@pytest.fixture
def staff_client(client, staff_user, password):
    client.login(username=staff_user.username, password=password)
    return client
