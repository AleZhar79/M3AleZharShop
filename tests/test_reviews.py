"""Тесты отзывов: добавление через форму на странице товара."""

from __future__ import annotations

import pytest

from apps.reviews.models import Review


@pytest.mark.django_db
def test_add_review_requires_login(client, product):
    response = client.post(
        f"/reviews/product/{product.slug}/add/",
        data={"rating": 5, "comment": "Топ"},
    )
    # Анонимного редиректит на login.
    assert response.status_code in (302, 303)
    assert "/account/login/" in response["Location"]
    assert Review.objects.count() == 0


@pytest.mark.django_db
def test_authenticated_user_can_add_review(auth_client, product, user):
    response = auth_client.post(
        f"/reviews/product/{product.slug}/add/",
        data={"rating": 4, "comment": "Норм"},
        follow=True,
    )
    assert response.status_code == 200
    assert Review.objects.filter(product=product, user=user).count() == 1


@pytest.mark.django_db(transaction=True)
def test_user_cannot_add_two_reviews_to_same_product(auth_client, product):
    auth_client.post(
        f"/reviews/product/{product.slug}/add/",
        data={"rating": 4, "comment": "Первый"},
    )
    auth_client.post(
        f"/reviews/product/{product.slug}/add/",
        data={"rating": 1, "comment": "Второй"},
    )
    # Только один отзыв в БД.
    assert Review.objects.filter(product=product).count() == 1


@pytest.mark.django_db
def test_invalid_rating_does_not_create_review(auth_client, product):
    auth_client.post(
        f"/reviews/product/{product.slug}/add/",
        data={"rating": 99, "comment": "Не должно пройти"},
    )
    assert Review.objects.count() == 0
