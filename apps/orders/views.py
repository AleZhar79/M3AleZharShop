"""Представления приложения orders."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.cart import Cart

from .forms import OrderCreateForm
from .models import Order
from .services import EmptyCartError, OutOfStockError, place_order, send_order_confirmation


@login_required
def order_create(request: HttpRequest) -> HttpResponse:
    """GET — показать форму оформления. POST — создать заказ."""
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, "Корзина пуста — добавьте товары перед оформлением.")
        return redirect("products:product-list")

    initial = {
        "customer_name": (request.user.get_full_name() or request.user.username),
        "contact_email": request.user.email,
    }
    form = OrderCreateForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        try:
            order = place_order(
                user=request.user,
                cart=cart,
                form_data=form.cleaned_data,
            )
        except EmptyCartError:
            messages.error(request, "Корзина пуста.")
            return redirect("cart:detail")
        except OutOfStockError as exc:
            messages.error(request, f"Недостаточно товара на складе: {exc}")
            return redirect("cart:detail")

        send_order_confirmation(order, request=request)
        return redirect("orders:order-created", pk=order.pk)

    return render(request, "orders/order_create.html", {"form": form, "cart": cart})


@login_required
def order_created(request: HttpRequest, pk: int) -> HttpResponse:
    """Страница «спасибо» с подтверждением заказа."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "orders/order_created.html", {"order": order})
