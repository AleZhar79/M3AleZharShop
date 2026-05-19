"""Модели приложения orders: заказы и позиции заказа."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.products.models import Product, TimeStampedModel


class OrderStatus(models.TextChoices):
    """Допустимые статусы заказа.

    Используется ``TextChoices`` — статусы хранятся как строки в БД,
    что упрощает чтение SQL и интеграции.
    """

    PENDING = "pending", "Ожидает оплаты"
    PAID = "paid", "Оплачен"
    SHIPPED = "shipped", "Отправлен"
    DELIVERED = "delivered", "Доставлен"
    CANCELLED = "cancelled", "Отменён"


class Order(TimeStampedModel):
    """Заказ пользователя.

    ``total_price`` хранится как снимок — он считается на момент оформления
    из ``OrderItem.price * quantity``; цены в каталоге могут меняться, но
    в заказе остаются исторические.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    total_price = models.DecimalField(
        "Итоговая сумма",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    customer_name = models.CharField("Имя получателя", max_length=150, blank=True)
    shipping_address = models.TextField("Адрес доставки", blank=True)
    contact_phone = models.CharField("Телефон для связи", max_length=32, blank=True)
    contact_email = models.EmailField("Email для связи", blank=True)
    comment = models.TextField("Комментарий к заказу", blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("user", "-created_at")),
            models.Index(fields=("status",)),
        ]

    def __str__(self) -> str:
        return f"Заказ #{self.pk} ({self.get_status_display()})"

    def recalculate_total(self) -> Decimal:
        """Пересчитать итог по позициям. На Шаге 4 будет вызван из бизнес-логики."""
        total = sum(
            (item.price * item.quantity for item in self.items.all()),
            start=Decimal("0.00"),
        )
        self.total_price = total
        return total


class OrderItem(models.Model):
    """Позиция заказа — товар + количество + цена-снимок."""

    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField("Количество", default=1)
    price = models.DecimalField(
        "Цена за единицу (снимок)",
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        constraints = [
            models.UniqueConstraint(
                fields=("order", "product"),
                name="unique_product_per_order",
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gte=1),
                name="orderitem_quantity_gte_1",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product} × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        """Стоимость позиции = цена × количество."""
        return self.price * self.quantity
