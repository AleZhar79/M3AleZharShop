"""Представления приложения products."""

from __future__ import annotations

from typing import Any

from django.db.models import Avg, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from apps.cart.forms import CartAddProductForm
from apps.products.forms import ProductFilterForm
from apps.products.models import Category, Product
from apps.reviews.forms import ReviewForm

DEFAULT_SORT = "-created_at"


class ProductListView(ListView):
    """Список товаров с поиском, фильтрами, сортировкой и пагинацией.

    Источник параметров — GET-строка (``?q=...&category=...&sort=...&page=...``).
    Параметры проходят через ``ProductFilterForm``, что даёт защиту от
    некорректных значений (например, ``sort=DROP TABLE``).
    """

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self) -> QuerySet[Product]:
        qs = Product.objects.filter(is_active=True).select_related("category")
        form = self._get_filter_form()
        if not form.is_valid():
            # Невалидная форма — игнорируем фильтры, отдаём всё.
            return qs.order_by(DEFAULT_SORT)

        data = form.cleaned_data

        if q := data.get("q"):
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        if category := data.get("category"):
            qs = qs.filter(category=category)
        if (price_min := data.get("price_min")) is not None:
            qs = qs.filter(price__gte=price_min)
        if (price_max := data.get("price_max")) is not None:
            qs = qs.filter(price__lte=price_max)

        sort = data.get("sort") or DEFAULT_SORT
        return qs.order_by(sort)

    def _get_filter_form(self) -> ProductFilterForm:
        # Кэшируем форму на запрос, чтобы не пересоздавать в get_context_data.
        if not hasattr(self, "_filter_form_cache"):
            self._filter_form_cache = ProductFilterForm(self.request.GET or None)
        return self._filter_form_cache

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = self._get_filter_form()
        # GET-параметры без 'page' — чтобы корректно строить ссылки пагинации.
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        return ctx


class CategoryDetailView(ProductListView):
    """Список товаров одной категории. Шаблон тот же, что у каталога."""

    template_name = "products/product_list.html"

    def get_queryset(self) -> QuerySet[Product]:
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["current_category"] = self.category
        return ctx


class ProductDetailView(DetailView):
    """Детальная страница товара: описание, отзывы, кнопка «в корзину»."""

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.filter(is_active=True).select_related("category")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        product: Product = ctx["product"]
        reviews = product.reviews.select_related("user").order_by("-created_at")
        agg = reviews.aggregate(avg=Avg("rating"))
        ctx["reviews"] = reviews
        ctx["avg_rating"] = agg["avg"]
        ctx["reviews_count"] = reviews.count()
        ctx["cart_form"] = CartAddProductForm()

        user = self.request.user
        if user.is_authenticated:
            ctx["user_already_reviewed"] = reviews.filter(user=user).exists()
            ctx["review_form"] = ReviewForm()
        else:
            ctx["user_already_reviewed"] = False
            ctx["review_form"] = None
        return ctx
