"""django-filter фильтры для REST API."""
from __future__ import annotations

import django_filters as df

from apps.products.models import Product


class ProductFilter(df.FilterSet):
    """Фильтр товаров: по цене, категории, активности и наличию."""

    min_price = df.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = df.NumberFilter(field_name="price", lookup_expr="lte")
    category = df.CharFilter(field_name="category__slug", lookup_expr="iexact")
    in_stock = df.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ("category", "is_active", "min_price", "max_price", "in_stock")

    def filter_in_stock(self, queryset, name: str, value: bool):
        if value is True:
            return queryset.filter(stock__gt=0)
        if value is False:
            return queryset.filter(stock=0)
        return queryset
