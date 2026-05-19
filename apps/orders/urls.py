"""Маршруты приложения orders."""
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.order_create, name="order-create"),
    path("created/<int:pk>/", views.order_created, name="order-created"),
]
