# M3AleZharShop

Интернет-магазин на Django/DRF. Учебный проект (ТЗ — `06-Project-M3-1.md`).

> **Статус:** Шаг 1 — каркас проекта. Подняты Django + PostgreSQL в Docker
> Compose, созданы пустые приложения `users`, `products`, `orders`, `reviews`.
> Бизнес-логика, REST API, шаблоны и т.д. будут добавляться на следующих шагах.

---

## Стек

- Python 3.12
- Django 5.x
- PostgreSQL 16
- Docker / Docker Compose
- (далее) DRF, SimpleJWT, drf-spectacular, pytest-django, flake8, mypy

---

## Структура проекта

```
M3AleZharShop/
├── config/                 # settings, urls, wsgi/asgi
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── __init__.py
│   ├── users/              # пользователи, регистрация, профили
│   ├── products/           # каталог: категории и товары
│   ├── orders/             # заказы и корзина
│   └── reviews/            # отзывы
├── templates/              # Django-шаблоны (пока пусто)
├── static/                 # статика (пока пусто)
├── media/                  # загружаемые файлы
├── tests/                  # тесты
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
└── README.md
```

---

## Быстрый запуск (Docker)

### 1. Подготовьте `.env`

```bash
cp .env.example .env
```

При необходимости отредактируйте значения (как минимум — `DJANGO_SECRET_KEY`
в продакшене).

### 2. Соберите и запустите контейнеры

```bash
docker compose build
docker compose up -d
```

Поднимутся два сервиса:

- `db` — PostgreSQL 16 (порт хоста `55432` по умолчанию, чтобы не конфликтовать с локальным PostgreSQL)
- `web` — Django (порт хоста `8000` по умолчанию)

### 3. Примените миграции и создайте суперпользователя

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### 4. Проверьте, что всё работает

- Healthcheck: <http://127.0.0.1:8000/> → должен вернуть `OK`
- Админка: <http://127.0.0.1:8000/admin/>
- Дашборд аналитики (только для staff): <http://127.0.0.1:8000/admin/dashboard/>
- REST API + Swagger UI: <http://127.0.0.1:8000/api/docs/>
- ReDoc: <http://127.0.0.1:8000/api/redoc/>
- OpenAPI схема: <http://127.0.0.1:8000/api/schema/>

На дашборде:
- KPI: выручка, всего заказов, оплаченных, средний чек, товаров в каталоге,
  нет в наличии, отзывов всего.
- Топ-10 товаров по выручке (только оплаченные/отправленные/доставленные).
- Распределение заказов по статусам.
- Продажи по дням.
- Список товаров с низкими остатками (≤ 5).
- Период выбирается через `?days=7|30|90|180|365`.

В админке заказов появились массовые действия: «Отметить как оплаченные»,
«Отметить как отправленные», «Отметить как доставленные», «Отменить заказы».
В админке товаров — «Скрыть из каталога» и «Вернуть в каталог».

### REST API (Шаг 8)

Все эндпоинты живут под `адрес/api/`. Аутентификация — JWT (SimpleJWT),
документация — OpenAPI 3 через drf-spectacular.

**Аутентификация:**
- `POST /api/auth/register/` — регистрация.
- `POST /api/auth/token/` — получить access+refresh.
- `POST /api/auth/token/refresh/` — обновить access.
- `POST /api/auth/token/verify/` — проверить токен.
- `GET  /api/auth/me/` — текущий пользователь.

**Ресурсы:**
- `GET /api/products/` — список товаров, фильтры `?category=`, `?min_price=`, `?max_price=`,
  `?in_stock=`, `?search=`, `?ordering=price|-price|name|...`, пагинация.
- `GET /api/products/{slug}/` — детальная карточка.
- `GET|POST /api/products/{slug}/reviews/` — отзывы к товару (POST — только авторизованные).
- `GET /api/categories/` и `GET /api/categories/{slug}/`.
- `GET|POST|PATCH|DELETE /api/reviews/` — CRUD отзывов (изменять/удалять может только автор).
- `GET|POST /api/orders/` — список и создание заказов (только свои).

**Пример создания заказа:**

```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer <ACCESS>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Иван Петров",
    "shipping_address": "СПб, Невский 1",
    "contact_phone": "+79990000000",
    "contact_email": "ivan@example.com",
    "items": [{"product": 1, "quantity": 2}, {"product": 5, "quantity": 1}]
  }'
```

Цена позиции берётся из `Product.price` на момент оформления (цена-снимок),
остатки списываются в транзакции с `SELECT FOR UPDATE`.

### Если порт PostgreSQL уже занят

Ошибка `Bind for 0.0.0.0:XXXX failed: port is already allocated` означает,
что на хосте уже работает другой PostgreSQL. Часто бывают заняты
и 5432, и 5433. Поэтому в `.env.example` по умолчанию `POSTGRES_PORT_HOST=55432`
— высокий нестандартный порт, который почти всегда свободен. Если и он
занят — поставьте в `.env` любой другой (например, `15432`, `25432`).
Внутри `docker compose` сервис `web` всё равно ходит к `db:5432`.

Проверить, свободен ли порт (PowerShell):

```powershell
netstat -ano | findstr ":55432"
```

Пустой вывод = порт свободен.

### Полезные команды

```bash
# Логи приложения
docker compose logs -f web

# Логи БД
docker compose logs -f db

# Открыть shell внутри контейнера
docker compose exec web bash

# Django shell
docker compose exec web python manage.py shell

# Остановить и удалить контейнеры
docker compose down

# Полностью сбросить (включая том с данными БД)
docker compose down -v
```

---

## Запуск без Docker (опционально, для разработки)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# В .env установите POSTGRES_HOST=localhost (если PostgreSQL поднят локально)

python manage.py migrate
python manage.py runserver
```

---

## Дорожная карта

- [x] Шаг 1: каркас проекта, Docker, PostgreSQL, пустые приложения
- [x] Шаг 2: модели `Category`, `Product`, `Order`, `OrderItem`, `Review`
- [x] Шаг 3: каталог, фильтры, поиск, пагинация
- [x] Шаг 4: страница товара, отзывы, корзина
- [x] Шаг 5: оформление заказа и email-уведомления
- [x] Шаг 6: личный кабинет, история заказов, аутентификация
- [x] Шаг 7: расширенная админка и дашборд аналитики
- [x] Шаг 8: REST API + JWT + Swagger
- [ ] Шаг 9: линтеры, типизация, тесты
- [ ] (Бонус) GraphQL, CI/CD

---

## Лицензия и автор

Учебный проект. Автор: Aleksei Zharkov (AleZhar).
