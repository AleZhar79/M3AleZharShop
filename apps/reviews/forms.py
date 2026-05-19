"""Формы приложения reviews."""
from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    """Форма отзыва. ``product`` и ``user`` ставятся во view."""

    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Поделитесь впечатлениями…"}),
        }
        labels = {
            "rating": "Оценка",
            "comment": "Комментарий",
        }
