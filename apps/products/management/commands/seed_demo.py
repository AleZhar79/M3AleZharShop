"""Management-команда: наполнить каталог демо-данными.

Использование (в Docker):
    docker compose exec web python manage.py seed_demo
    docker compose exec web python manage.py seed_demo --reset  # очистить и заново

Идемпотентна: повторный запуск без --reset не плодит дубликаты,
а обновляет существующие записи по slug.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand

from apps.products.models import Category, Product

CATEGORIES: list[dict[str, Any]] = [
    {"name": "Хмель", "slug": "hops"},
    {"name": "Солод", "slug": "malt"},
    {"name": "Дрожжи", "slug": "yeast"},
    {"name": "Оборудование", "slug": "equipment"},
]

# slug всегда ASCII — это стандартный path-converter <slug:...>
# и в целом лучшая практика для URL.
PRODUCTS: list[dict[str, Any]] = [
    {"slug": "hops-citra-100g",      "name": "Хмель Citra 100 г",      "category": "hops",      "price": "490.00",  "stock": 50,  "description": "Ароматный американский хмель. Цитрусовые ноты."},
    {"slug": "hops-mosaic-100g",     "name": "Хмель Mosaic 100 г",     "category": "hops",      "price": "520.00",  "stock": 30,  "description": "Тропические фрукты, манго, ананас."},
    {"slug": "hops-saaz-100g",       "name": "Хмель Saaz 100 г",       "category": "hops",      "price": "380.00",  "stock": 80,  "description": "Классический чешский хмель для лагеров."},
    {"slug": "hops-cascade-100g",    "name": "Хмель Cascade 100 г",    "category": "hops",      "price": "350.00",  "stock": 100, "description": "Универсальный хмель, цитрусовая горечь."},
    {"slug": "malt-pilsner-1kg",     "name": "Солод Pilsner 1 кг",     "category": "malt",      "price": "180.00",  "stock": 200, "description": "Базовый солод для светлых стилей."},
    {"slug": "malt-vienna-1kg",      "name": "Солод Vienna 1 кг",      "category": "malt",      "price": "210.00",  "stock": 120, "description": "Среднецветный солод, хлебные тона."},
    {"slug": "malt-caramel-60-1kg",  "name": "Солод Caramel 60 1 кг",  "category": "malt",      "price": "260.00",  "stock": 60,  "description": "Карамельный солод, повышает плотность."},
    {"slug": "yeast-us-05",          "name": "Дрожжи US-05 11.5 г",    "category": "yeast",     "price": "390.00",  "stock": 40,  "description": "Сухие элевые дрожжи, чистый профиль."},
    {"slug": "yeast-s-04",           "name": "Дрожжи S-04 11.5 г",     "category": "yeast",     "price": "410.00",  "stock": 35,  "description": "Английский эль, фруктовые эфиры."},
    {"slug": "yeast-w-34-70",        "name": "Дрожжи W-34/70 11.5 г",  "category": "yeast",     "price": "430.00",  "stock": 25,  "description": "Низовые лагерные дрожжи."},
    {"slug": "eq-fermenter-30l",     "name": "Бродильная ёмкость 30 л", "category": "equipment", "price": "3490.00", "stock": 8,   "description": "Пластиковый бак с гидрозатвором."},
    {"slug": "eq-hydrometer",        "name": "Ареометр сахарометр",    "category": "equipment", "price": "690.00",  "stock": 15,  "description": "Для измерения начальной плотности сусла."},
    {"slug": "eq-chiller",           "name": "Чиллер погружной",       "category": "equipment", "price": "5290.00", "stock": 4,   "description": "Медный чиллер для охлаждения сусла."},
    {"slug": "eq-siphon",            "name": "Сифон с краном",         "category": "equipment", "price": "890.00",  "stock": 20,  "description": "Для розлива готового пива по бутылкам."},
    {"slug": "eq-thermometer",       "name": "Термометр цифровой",     "category": "equipment", "price": "550.00",  "stock": 30,  "description": "Диапазон 0–100°C, щуп-игла."},
]


class Command(BaseCommand):
    """Создать демонстрационные категории и товары."""

    help = "Создать демо-данные каталога (категории + товары)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить все существующие товары и категории перед загрузкой.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["reset"]:
            deleted_products = Product.objects.all().delete()[0]
            deleted_categories = Category.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(
                    f"Удалено товаров: {deleted_products}, категорий: {deleted_categories}"
                )
            )

        # Категории
        cat_by_slug: dict[str, Category] = {}
        for data in CATEGORIES:
            cat, created = Category.objects.update_or_create(
                slug=data["slug"],
                defaults={"name": data["name"]},
            )
            cat_by_slug[data["slug"]] = cat
            verb = "создана" if created else "обновлена"
            self.stdout.write(f"Категория {verb}: {cat.name}")

        # Товары. slug задан явно в PRODUCTS — идемпотентно.
        created_count = 0
        updated_count = 0
        for data in PRODUCTS:
            _, created = Product.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "price": Decimal(data["price"]),
                    "category": cat_by_slug[data["category"]],
                    "stock": data["stock"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Товаров создано: {created_count}, обновлено: {updated_count}."
            )
        )
