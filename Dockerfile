# --- Базовый образ ---
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# На Шаге 1 системные пакеты не нужны: psycopg[binary] и Django ставятся
# из готовых wheel-ов без компиляции. Когда понадобится Pillow / psycopg
# из исходников — добавим build-essential и libpq-dev отдельным слоем.

WORKDIR /app

# Сначала зависимости (для кэша)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Затем исходники
COPY . /app

EXPOSE 8000

# В Шаге 1 — dev-режим через runserver (удобно для проверки)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
