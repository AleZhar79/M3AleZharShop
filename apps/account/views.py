"""Представления личного кабинета."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from apps.orders.models import Order

from .forms import ProfileEditForm, SignupForm


def signup(request: HttpRequest) -> HttpResponse:
    """Регистрация с автоматическим входом после успеха."""
    if request.user.is_authenticated:
        return redirect("account:profile")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Добро пожаловать, {user.username}.")
        return redirect("account:profile")
    return render(request, "account/signup.html", {"form": form})


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """Краткая сводка профиля + последние 5 заказов."""
    recent_orders = Order.objects.filter(user=request.user).order_by("-created_at")[:5]
    return render(
        request,
        "account/profile.html",
        {"recent_orders": recent_orders},
    )


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование first_name / last_name / email."""

    form_class = ProfileEditForm
    template_name = "account/profile_edit.html"
    success_url = reverse_lazy("account:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлён.")
        return super().form_valid(form)


class OrderListView(LoginRequiredMixin, ListView):
    """История заказов пользователя."""

    template_name = "account/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Деталь заказа — только владельцу."""

    template_name = "account/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")
