# Org Structure API

REST API для управления организационной структурой: подразделения (Department) и сотрудники (Employee).

## Стек

| Слой | Технология |
|------|-----------|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2 (async) |
| БД | PostgreSQL 16 |
| Миграции | Alembic |
| Контейнеризация | Docker + docker-compose |
| Тесты | pytest + pytest-asyncio |

## Структура проекта

```
org_api/
├── app/
│   ├── api/v1/endpoints/   # FastAPI-роутеры (тонкий слой)
│   ├── core/               # Конфигурация, логирование
│   ├── db/                 # Движок SQLAlchemy, сессия
│   ├── models/             # ORM-модели
│   ├── schemas/            # Pydantic-схемы (запросы / ответы)
│   ├── services/           # Бизнес-логика
│   └── main.py             # Точка входа
├── alembic/                # Миграции
├── tests/                  # pytest-тесты
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Быстрый старт

1. 
```bash
git clone https://github.com/antonVosc/org_api.git
```

2. 
```bash
cd org_api/
```

3. 
```bash
docker-compose up --build
```

Приложение будет доступно по адресу: **http://localhost:8000**

Интерактивная документация: **http://localhost:8000/docs**

## Запуск тестов

```bash
docker-compose --profile test run --rm test
```

## Создание департамента

```bash
curl -X POST http://localhost:8000/api/v1/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering"}'
```

```bash
curl -X POST http://localhost:8000/api/v1/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Backend", "parent_id": 1}'
```

## Создание департамента

```bash
curl -X POST http://localhost:8000/api/v1/departments/1/employees/ \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Doe", "position": "Developer"}'
```

## Детали департамента

```bash
curl http://localhost:8000/api/v1/departments/1
```

## Детали департамента с детьми

```bash
curl "http://localhost:8000/api/v1/departments/1?depth=2"
```

## Запуск тестов

```bash
docker-compose --profile test run --rm test
```

## API

### Подразделения

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/api/v1/departments/` | Создать подразделение |
| `GET` | `/api/v1/departments/{id}` | Получить подразделение с сотрудниками и поддеревом |
| `PATCH` | `/api/v1/departments/{id}` | Обновить имя / переместить |
| `DELETE` | `/api/v1/departments/{id}` | Удалить (`cascade` или `reassign`) |
| `POST` | `/api/v1/departments/{id}/employees/` | Добавить сотрудника |

### Параметры GET /departments/{id}

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `depth` | int | 1 | Глубина вложенных подразделений (1–5) |
| `include_employees` | bool | true | Включать ли список сотрудников |

### Параметры DELETE /departments/{id}

| Параметр | Тип | Описание |
|----------|-----|----------|
| `mode` | `cascade` \| `reassign` | Режим удаления |
| `reassign_to_department_id` | int | Обязателен при `mode=reassign` |

## Бизнес-правила

- Имя подразделения: 1–200 символов, trim пробелов, уникальность в рамках одного родителя.
- Нельзя сделать подразделение родителем самого себя — **409 Conflict**.
- Нельзя создать цикл в дереве — **409 Conflict**.
- Сотрудник в несуществующем подразделении — **404 Not Found**.
- `mode=cascade` — каскадное удаление всего поддерева и сотрудников.
- `mode=reassign` — сотрудники переводятся в `reassign_to_department_id`, дочерние подразделения поднимаются на уровень удалённого.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://orguser:orgpass@db:5432/orgdb` | DSN БД |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `POSTGRES_USER` | `orguser` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | `orgpass` | Пароль PostgreSQL |
| `POSTGRES_DB` | `orgdb` | Имя базы данных |
