# Job Tracker

Сервис для учёта откликов на вакансии. Пользователь регистрируется, ведёт список вакансий со статусами и видит статистику и историю действий.

Проект сделан как pet-проект для демонстрации backend-навыков: REST API, фоновые задачи, события, кеш, мониторинг и деплой.

## Стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic
- **Данные:** PostgreSQL 18, Redis 7 (кеш, блокировки, лимиты, статистика)
- **Фоновые задачи:** Celery + RabbitMQ 4
- **События:** Kafka (два независимых консьюмера: история действий и инсайты)
- **Авторизация:** JWT, bcrypt, ограничение числа попыток входа
- **Мониторинг:** метрики FastAPI, Prometheus, экспортеры, Grafana (дашборд хранится в репозитории)
- **Инфраструктура:** Docker Compose, Caddy (HTTPS), GitHub Actions (тесты и проверка миграций)

## Архитектура

```
Браузер ──HTTPS──► Caddy ──► FastAPI (API + статика фронтенда)
                              │  ├─ PostgreSQL   (вакансии, пользователи)
                              │  ├─ Redis        (кеш, блокировки, лимиты)
                              │  ├─ RabbitMQ ──► Celery worker (пересчёт статистики)
                              │  └─ Kafka ──► history-consumer, insights-consumer
Prometheus ◄── метрики ── API, RabbitMQ, Redis, PostgreSQL, Celery   (профиль monitoring)
Grafana    ◄── Prometheus                                            (профиль monitoring)
```

Список вакансий не ждёт пересчёта статистики: расчёт уходит в фоновую задачу. Redis-блокировка на 60 секунд не даёт ставить дубликаты задач для одного пользователя.

## Локальный запуск

```bash
cp .env.example .env          # заполните пароли и SECRET_KEY, ENABLE_DOCS=true для Swagger
docker compose up -d --build
```

- Фронтенд: http://localhost:8000
- Swagger (при `ENABLE_DOCS=true`): http://localhost:8000/docs
- Мониторинг: `docker compose --profile monitoring up -d`, Grafana на http://localhost:3000

Ключ `SECRET_KEY` генерируется командой `python -c "import secrets; print(secrets.token_hex(32))"`.

## Тесты

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

Тесты используют SQLite в памяти и fakeredis, внешние сервисы для них не нужны. В CI дополнительно проверяются миграции Alembic и `alembic check`.

## Деплой

Сервер: Linux с Docker и Docker Compose, домен, направленный на IP сервера.

```bash
git clone https://github.com/YAroslav10Ti/job-tracker.git /opt/job-tracker
cd /opt/job-tracker
cp .env.example .env          # DOMAIN=ваш.домен, новые пароли, ENABLE_DOCS=false
docker compose --profile prod up -d --build
```

Caddy получает сертификат Let's Encrypt автоматически. Порты баз данных и брокеров привязаны к `127.0.0.1` и наружу не открыты.

Бэкап базы: `scripts/backup.sh` (дамп в `backups/`, cron-строка в начале файла). Восстановление проверено на тестовой базе.

## Демо

Демо-аккаунт: `demo@ваш.домен` / пароль: `____`. Регистрация на демо-сервере отключена.

## Что не сделано

- Нет высокой доступности: один сервер, одна копия каждого сервиса.
- Нет автоматического деплоя (CD): выкладка вручную по командам выше.
- Нет интеграционных тестов с реальными PostgreSQL, Redis и Kafka в CI.
