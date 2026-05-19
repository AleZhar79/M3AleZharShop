"""Маршрутизация REST API.

Все эндпоинты живут под префиксом ``/api/``. JWT-аутентификация
реализована поверх SimpleJWT, документация — drf-spectacular.
"""

from __future__ import annotations

from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    CategoryViewSet,
    MeView,
    OrderViewSet,
    ProductViewSet,
    RegisterView,
    ReviewViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    # Аутентификация JWT
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    # OpenAPI / Swagger / Redoc
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="docs"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
    # CRUD ресурсы
    path("", include(router.urls)),
]
