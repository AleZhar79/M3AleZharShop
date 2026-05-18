"""Корневая маршрутизация проекта."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import path


def healthcheck(_request: HttpRequest) -> HttpResponse:
    """Простой эндпоинт для проверки, что приложение поднялось."""
    return HttpResponse("OK", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", healthcheck, name="healthcheck"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
