"""Формы корзины."""
from django import forms


PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]


class CartAddProductForm(forms.Form):
    """Форма добавления товара в корзину со страницы товара."""

    quantity = forms.TypedChoiceField(
        label="Количество",
        choices=PRODUCT_QUANTITY_CHOICES,
        coerce=int,
        initial=1,
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput,
    )


class CartUpdateForm(forms.Form):
    """Ручное изменение количества с самой страницы корзины."""

    quantity = forms.IntegerField(min_value=1, max_value=99)
