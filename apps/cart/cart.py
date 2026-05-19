"""Сессионная корзина.

Хранит позиции в ``request.session[settings.CART_SESSION_KEY]`` как словарь
``{"<product_id>": {"quantity": int, "price": "<decimal-str>"}}``. Цена
фиксируется в момент добавления, чтобы изменение каталога не влияло на
уже добавленные в корзину товары.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Iterator

from django.conf import settings

from apps.products.models import Product

CART_SESSION_KEY = "cart"


class Cart:
    def __init__(self, request) -> None:
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not cart:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart: dict[str, dict[str, str | int]] = cart

    # ---- Мутации ---------------------------------------------------------
    def add(self, product: Product, quantity: int = 1, override: bool = False) -> None:
        """Добавить товар или увеличить количество.

        ``override=True`` — заменить количество (используется со страницы
        корзины при ручном изменении). Количество не может стать меньше 1
        или превысить остаток на складе.
        """
        pid = str(product.pk)
        if pid not in self.cart:
            self.cart[pid] = {"quantity": 0, "price": str(product.price)}
        if override:
            self.cart[pid]["quantity"] = int(quantity)
        else:
            self.cart[pid]["quantity"] = int(self.cart[pid]["quantity"]) + int(quantity)

        # Защита от выхода за пределы остатка и нулевого/отрицательного значения.
        qty = int(self.cart[pid]["quantity"])
        if qty < 1:
            self.remove(product)
            return
        if product.stock and qty > product.stock:
            self.cart[pid]["quantity"] = int(product.stock)
        # Обновляем цену на актуальную (можно изменить политику позже).
        self.cart[pid]["price"] = str(product.price)
        self.save()

    def remove(self, product: Product) -> None:
        pid = str(product.pk)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self) -> None:
        self.session[CART_SESSION_KEY] = {}
        self.cart = self.session[CART_SESSION_KEY]
        self.save()

    def save(self) -> None:
        self.session.modified = True

    # ---- Чтение ----------------------------------------------------------
    def __iter__(self) -> Iterator[dict]:
        """Итерация по позициям с подгрузкой Product одним запросом."""
        ids = [int(pid) for pid in self.cart.keys()]
        products = {p.pk: p for p in Product.objects.filter(pk__in=ids)}
        for pid, item in self.cart.items():
            product = products.get(int(pid))
            if product is None:
                continue
            quantity = int(item["quantity"])
            price = Decimal(str(item["price"]))
            yield {
                "product": product,
                "quantity": quantity,
                "price": price,
                "total_price": price * quantity,
            }

    def __len__(self) -> int:
        return sum(int(item["quantity"]) for item in self.cart.values())

    @property
    def total_price(self) -> Decimal:
        return sum(
            (Decimal(str(item["price"])) * int(item["quantity"]) for item in self.cart.values()),
            Decimal("0.00"),
        )

    @property
    def is_empty(self) -> bool:
        return not self.cart
