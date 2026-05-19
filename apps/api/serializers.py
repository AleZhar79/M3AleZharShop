"""Сериализаторы для REST API.

Главное правило: сериализаторы для записи и чтения максимально явные —
никаких ``fields = '__all__'``. Это защищает от случайного раскрытия
служебных полей и упрощает версионирование API.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from apps.orders.models import Order, OrderItem, OrderStatus
from apps.products.models import Category, Product
from apps.reviews.models import Review

User = get_user_model()


# --- Пользователи ---------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    """Профиль пользователя — read-only выдача."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации.

    Пароль валидируется штатными валидаторами Django и хешируется
    через ``User.objects.create_user``.
    """

    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")
        extra_kwargs = {
            "email": {"required": True},
        }

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data: dict):
        return User.objects.create_user(**validated_data)


# --- Категории и товары ---------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    """Короткая выдача категорий — для каталога."""

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent")
        read_only_fields = fields


class ProductListSerializer(serializers.ModelSerializer):
    """Карточка товара в списке: минимум, чтобы быстрее отдавать."""

    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "stock",
            "is_active",
            "category",
            "image",
        )
        read_only_fields = fields


class ProductDetailSerializer(ProductListSerializer):
    """Подробная карточка товара с описанием и датами."""

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


# --- Отзывы ---------------------------------------------------------------
class ReviewSerializer(serializers.ModelSerializer):
    """Отзывы к товарам.

    ``user`` всегда подставляется из запроса. ``product`` обязателен только
    при создании верхнеуровневого ``/api/reviews/``; вложенный роут
    ``/api/products/{slug}/reviews/`` сам прокинет товар через view.
    """

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "product",
            "user",
            "user_username",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "user", "user_username", "created_at")
        extra_kwargs = {
            "product": {"required": False},
        }

    def validate_rating(self, value: int) -> int:
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Рейтинг должен быть от 1 до 5.")
        return value

    def validate(self, attrs: dict) -> dict:
        # При создании через /api/reviews/ product должен быть передан явно.
        request = self.context.get("request")
        if request and request.method == "POST" and not self.context.get("product"):
            if not attrs.get("product"):
                raise serializers.ValidationError({"product": "Это поле обязательно."})
        return attrs

    def create(self, validated_data: dict) -> Review:
        request = self.context["request"]
        product = self.context.get("product") or validated_data.pop("product")
        return Review.objects.create(user=request.user, product=product, **validated_data)


# --- Заказы ---------------------------------------------------------------
class OrderItemReadSerializer(serializers.ModelSerializer):
    """Позиция в выдаче заказа."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "quantity", "price", "line_total")
        read_only_fields = fields

    def get_line_total(self, obj: OrderItem) -> str:
        return str(obj.price * obj.quantity)


class OrderItemWriteSerializer(serializers.Serializer):
    """Позиция в запросе на создание заказа.

    Цена не принимается с клиента — она всегда берётся из ``Product.price``
    на момент оформления (цена-снимок).
    """

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)


class OrderReadSerializer(serializers.ModelSerializer):
    """Подробное чтение заказа."""

    items = OrderItemReadSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "status",
            "status_display",
            "total_price",
            "customer_name",
            "shipping_address",
            "contact_phone",
            "contact_email",
            "comment",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    """Создание заказа: принимаем контактные данные + список items."""

    items = OrderItemWriteSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "customer_name",
            "shipping_address",
            "contact_phone",
            "contact_email",
            "comment",
            "items",
            "total_price",
            "status",
        )
        read_only_fields = ("id", "total_price", "status")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Заказ должен содержать хотя бы одну позицию.")
        # схлопываем дубли по product → суммируем quantity
        merged: dict = {}
        for it in value:
            pid = it["product"].pk
            merged[pid] = merged.get(pid, {"product": it["product"], "quantity": 0})
            merged[pid]["quantity"] += it["quantity"]
        return list(merged.values())

    @transaction.atomic
    def create(self, validated_data: dict) -> Order:
        from django.db.models import F  # локальный импорт, чтобы не путать с DRF F

        items = validated_data.pop("items")
        request = self.context["request"]

        # Блокируем товары и проверяем остатки.
        product_ids = [it["product"].pk for it in items]
        locked = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=product_ids)}
        for it in items:
            product = locked.get(it["product"].pk)
            if product is None or not product.is_active:
                raise serializers.ValidationError(
                    {"items": f"Товар id={it['product'].pk} недоступен."}
                )
            if product.stock < it["quantity"]:
                raise serializers.ValidationError(
                    {
                        "items": f"«{product.name}»: на складе {product.stock}, "
                        f"запрошено {it['quantity']}."
                    }
                )

        order = Order.objects.create(
            user=request.user,
            status=OrderStatus.PENDING,
            total_price=Decimal("0.00"),
            **validated_data,
        )

        total = Decimal("0.00")
        order_items: list[OrderItem] = []
        for it in items:
            product = locked[it["product"].pk]
            price = product.price
            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=it["quantity"],
                    price=price,
                )
            )
            total += price * it["quantity"]
        OrderItem.objects.bulk_create(order_items)

        # Списываем остатки атомарно
        for it in items:
            Product.objects.filter(pk=it["product"].pk).update(stock=F("stock") - it["quantity"])

        order.total_price = total
        order.save(update_fields=("total_price",))
        return order

    def to_representation(self, instance: Order) -> dict:
        # После create отдаём полную read-схему.
        return OrderReadSerializer(instance, context=self.context).data
