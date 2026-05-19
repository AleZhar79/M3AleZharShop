"""Корневая маршрутизация проекта."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Каталог — основной namespace 'products' на '/products/'.
    path("products/", include("apps.products.urls")),
    # Корзина.
    path("cart/", include("apps.cart.urls")),
    # Отзывы.
    path("reviews/", include("apps.reviews.urls")),
    # Заказы.
    path("orders/", include("apps.orders.urls")),
    # Личный кабинет.
    path("account/", include("apps.account.urls")),
    # Главная страница '/' ведёт в каталог.
    path("", RedirectView.as_view(pattern_name="products:product-list", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
