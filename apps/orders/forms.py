"""Формы приложения orders."""

from __future__ import annotations

from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    """Форма оформления заказа.

    ``user`` и ``total_price`` не вводятся пользователем — ставятся во view.
    """

    class Meta:
        model = Order
        fields = (
            "customer_name",
            "contact_email",
            "contact_phone",
            "shipping_address",
            "comment",
        )
        widgets = {
            "shipping_address": forms.Textarea(attrs={"rows": 3}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Необязательно"}),
        }
        labels = {
            "customer_name": "ФИО получателя",
            "contact_email": "Email",
            "contact_phone": "Телефон",
            "shipping_address": "Адрес доставки",
            "comment": "Комментарий к заказу",
        }

    def clean_customer_name(self) -> str:
        value = self.cleaned_data["customer_name"].strip()
        if not value:
            raise forms.ValidationError("Укажите имя получателя.")
        return value

    def clean_contact_phone(self) -> str:
        value = self.cleaned_data["contact_phone"].strip()
        if not value:
            raise forms.ValidationError("Укажите телефон.")
        return value

    def clean_shipping_address(self) -> str:
        value = self.cleaned_data["shipping_address"].strip()
        if not value:
            raise forms.ValidationError("Укажите адрес доставки.")
        return value
