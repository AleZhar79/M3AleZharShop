"""Модели приложения products: каталог категорий и товаров."""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.urls import reverse


class TimeStampedModel(models.Model):
    """Абстрактная модель с полями ``created_at`` / ``updated_at``."""

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """Категория каталога. Поддерживает древовидную вложенность через ``parent``."""

    name = models.CharField("Название", max_length=150)
    slug = models.SlugField("Slug", max_length=160, unique=True)
    parent = models.ForeignKey(
        "self",
        verbose_name="Родительская категория",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ("name",)
        indexes = [models.Index(fields=("slug",))]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """URL страницы категории. Сам view появится на Шаге 3."""
        return reverse("products:category-detail", kwargs={"slug": self.slug})


class Product(TimeStampedModel):
    """Товар каталога."""

    name = models.CharField("Название", max_length=200)
    slug = models.SlugField("Slug", max_length=210, unique=True)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField(
        "Цена",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        on_delete=models.PROTECT,
        related_name="products",
    )
    image = models.ImageField("Изображение", upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField("Активен", default=True)
    stock = models.PositiveIntegerField("Остаток на складе", default=0)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("slug",)),
            models.Index(fields=("is_active",)),
            models.Index(fields=("category", "is_active")),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """URL страницы товара. Сам view появится на Шаге 3."""
        return reverse("products:product-detail", kwargs={"slug": self.slug})

    @property
    def in_stock(self) -> bool:
        """Есть ли товар в наличии."""
        return self.is_active and self.stock > 0
