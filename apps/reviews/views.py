"""Представления приложения reviews."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect

from apps.products.models import Product

from .forms import ReviewForm


@login_required
def add_review(request: HttpRequest, slug: str) -> HttpResponse:
    """Создать отзыв авторизованным пользователем.

    Один пользователь — один отзыв на товар (защита на уровне БД через
    UniqueConstraint). Повторная попытка приводит к понятному сообщению.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if request.method != "POST":
        return redirect(product.get_absolute_url())

    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Проверьте поля формы отзыва.")
        return redirect(product.get_absolute_url())

    review = form.save(commit=False)
    review.product = product
    review.user = request.user
    try:
        review.save()
        messages.success(request, "Спасибо за отзыв.")
    except IntegrityError:
        messages.warning(request, "Вы уже оставляли отзыв на этот товар.")
    return redirect(product.get_absolute_url())
