"""Представления корзины: add/update/remove/detail/clear."""
from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.products.models import Product

from .cart import Cart
from .forms import CartAddProductForm, CartUpdateForm


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd["quantity"], override=cd["override"])
        messages.success(request, f"«{product.name}» добавлен в корзину.")
    else:
        messages.error(request, "Не удалось добавить товар: неверные данные формы.")

    next_url = request.POST.get("next") or product.get_absolute_url()
    return redirect(next_url)


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = CartUpdateForm(request.POST)
    if form.is_valid():
        cart.add(product=product, quantity=form.cleaned_data["quantity"], override=True)
        messages.success(request, "Количество обновлено.")
    else:
        messages.error(request, "Неверное количество.")
    return redirect("cart:detail")


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f"«{product.name}» удалён из корзины.")
    return redirect("cart:detail")


@require_POST
def cart_clear(request: HttpRequest) -> HttpResponse:
    Cart(request).clear()
    messages.success(request, "Корзина очищена.")
    return redirect("cart:detail")


def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    return render(request, "cart/detail.html", {"cart": cart})
