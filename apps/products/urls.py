"""Маршруты приложения products."""

from django.urls import path

from apps.products import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product-list"),
    path("category/<slug:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("product/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
]
