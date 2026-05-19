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
- [ ] Шаг 4: страница товара, корзина, оформление заказа
- [ ] Шаг 5: личный кабинет, история заказов
- [ ] Шаг 6: админка с аналитикой
- [ ] Шаг 7: REST API + JWT + Swagger
- [ ] Шаг 8: линтеры, типизация, тесты
- [ ] (Бонус) GraphQL, CI/CD

---

## Лицензия и автор

Учебный проект. Автор: Aleksei Zharkov (AleZhar).
