"""Формы приложения products."""

from __future__ import annotations

from django import forms

from apps.products.models import Category


class ProductFilterForm(forms.Form):
    """Форма фильтрации каталога (GET-параметры).

    Все поля не обязательные: пустое значение трактуется как «без фильтра».
    Сортировка ограничена белым списком, чтобы не пропускать произвольные
    значения из URL в ``.order_by()``.
    """

    SORT_CHOICES = (
        ("-created_at", "Сначала новые"),
        ("created_at", "Сначала старые"),
        ("price", "Цена: по возрастанию"),
        ("-price", "Цена: по убыванию"),
        ("name", "Название: А → Я"),
        ("-name", "Название: Я → А"),
    )

    q = forms.CharField(
        label="Поиск",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Название или описание"}),
    )
    category = forms.ModelChoiceField(
        label="Категория",
        queryset=Category.objects.all().order_by("name"),
        required=False,
        empty_label="Все категории",
    )
    price_min = forms.DecimalField(
        label="Цена от",
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )
    price_max = forms.DecimalField(
        label="Цена до",
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
    )
    sort = forms.ChoiceField(
        label="Сортировка",
        choices=SORT_CHOICES,
        required=False,
        initial="-created_at",
    )
