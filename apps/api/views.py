"""Вьюхи REST API.

Большая часть эндпоинтов реализована через ``ReadOnlyModelViewSet`` или
``ModelViewSet``, что даёт нам list/retrieve/create/update/destroy
из коробки.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.products.models import Category, Product
from apps.reviews.models import Review

from .filters import ProductFilter
from .permissions import IsOwner, IsOwnerOrReadOnly
from .serializers import (
    CategorySerializer,
    OrderCreateSerializer,
    OrderReadSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    RegisterSerializer,
    ReviewSerializer,
    UserSerializer,
)


# --- Auth -----------------------------------------------------------------
class RegisterView(APIView):
    """Регистрация нового пользователя.

    После регистрации фронт обычно сам идёт за JWT через ``/api/auth/token/``.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserSerializer},
        description="Создаёт пользователя. Возвращает профиль без токена.",
    )
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """Текущий пользователь по JWT-токену."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    @extend_schema(responses={200: UserSerializer})
    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data)


# --- Categories -----------------------------------------------------------
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Только чтение — категории редактируются через админку."""

    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = "slug"


# --- Products -------------------------------------------------------------
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Каталог товаров: list, retrieve, фильтры, поиск, сортировка."""

    queryset = Product.objects.select_related("category").filter(is_active=True)
    permission_classes = (permissions.AllowAny,)
    lookup_field = "slug"
    filterset_class = ProductFilter
    search_fields = ("name", "description", "slug")
    ordering_fields = ("price", "created_at", "name", "stock")
    ordering = ("-created_at",)

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

    @extend_schema(
        responses={200: ReviewSerializer(many=True)},
        parameters=[
            OpenApiParameter("ordering", type=str, required=False),
        ],
    )
    @action(
        detail=True,
        methods=("get", "post"),
        url_path="reviews",
        permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
    )
    def reviews(self, request, slug: str | None = None):
        """Отзывы к товару: GET — список, POST — добавить (авторизованный)."""
        product = self.get_object()
        if request.method == "GET":
            qs = (
                Review.objects.filter(product=product)
                .select_related("user")
                .order_by("-created_at")
            )
            page = self.paginate_queryset(qs)
            serializer = ReviewSerializer(page or qs, many=True, context={"request": request})
            if page is not None:
                return self.get_paginated_response(serializer.data)
            return Response(serializer.data)

        # POST
        serializer = ReviewSerializer(
            data=request.data, context={"request": request, "product": product}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            ReviewSerializer(review, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# --- Reviews (верхнеуровневые) -------------------------------------------
class ReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Полный CRUD по отзывам с проверкой авторства."""

    queryset = Review.objects.select_related("product", "user").order_by("-created_at")
    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filterset_fields = ("product", "rating")
    search_fields = ("comment", "product__name")
    ordering_fields = ("created_at", "rating")


# --- Orders ---------------------------------------------------------------
class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Заказы пользователя.

    Видны только свои заказы. Создание идёт через ``OrderCreateSerializer``
    с проверкой остатков и атомарным списанием stock.
    """

    permission_classes = (permissions.IsAuthenticated, IsOwner)
    ordering_fields = ("created_at", "total_price")
    ordering = ("-created_at",)

    def get_queryset(self):
        user = self.request.user
        # Для генерации OpenAPI-схемы request может быть пустым.
        if not user or not user.is_authenticated:
            return Order.objects.none()
        return (
            Order.objects.filter(user=user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer
