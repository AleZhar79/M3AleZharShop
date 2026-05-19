"""Маршруты личного кабинета."""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "account"

urlpatterns = [
    # Аутентификация — встроенные view'ы Django со своими шаблонами.
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="account/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page=reverse_lazy("products:product-list")),
        name="logout",
    ),
    path("signup/", views.signup, name="signup"),
    # Личный кабинет.
    path("", views.profile, name="profile"),
    path("edit/", views.ProfileEditView.as_view(), name="profile-edit"),
    # История заказов.
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
]
