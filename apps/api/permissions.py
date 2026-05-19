"""Permission-классы для REST API."""

from __future__ import annotations

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Чтение всем, изменение — только автору объекта.

    Объект должен иметь поле ``user`` или ``author``.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "author", None)
        return bool(request.user and request.user.is_authenticated and owner == request.user)


class IsOwner(permissions.BasePermission):
    """Доступ только хозяину объекта.

    Используется, например, для заказов: чужие заказы вообще не показываем.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        owner = getattr(obj, "user", None)
        return bool(request.user and request.user.is_authenticated and owner == request.user)
