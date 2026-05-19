"""Модели приложения reviews: отзывы на товары."""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """Отзыв пользователя на товар.

    Один пользователь — один отзыв на товар (ограничение уровня БД).
    Проверка «отзыв можно оставить только после покупки» относится
    к бизнес-логике и будет реализована на Шаге 4 в форме/сериалайзере,
    а не на уровне модели.
    """

    product = models.ForeignKey(
        "products.Product",
        verbose_name="Товар",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        "Оценка",
        validators=(MinValueValidator(1), MaxValueValidator(5)),
    )
    comment = models.TextField("Комментарий", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("product", "user"),
                name="unique_review_per_user_product",
            ),
            models.CheckConstraint(
                check=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_1_to_5",
            ),
        ]
        indexes = [
            models.Index(fields=("product", "-created_at")),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.product} ({self.rating}/5)"
