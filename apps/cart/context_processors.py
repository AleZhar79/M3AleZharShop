"""Контекст-процессор: добавляет корзину в каждый шаблон."""

from .cart import Cart


def cart(request):
    return {"cart": Cart(request)}
