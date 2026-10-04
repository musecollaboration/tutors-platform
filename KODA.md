# KODA.md

Контекст проекта. Правила — в `.kodarules` и скиллах `.koda/skills/`.

## Приоритет источников

При конфликте: **документация библиотеки → `.kodarules` → скиллы → `KODA.md`**.

Документация библиотеки задаёт синтаксис API, `.kodarules` — правила проекта, скиллы — паттерны, `KODA.md` — контекст и структуру. Если пример из скилла расходится с документацией — верь документации и обновляй скилл.

## О проекте

**Название:** tutors-platform
**Домен:** платформа репетиторов
**Стадия:** разработка

Платформа для поиска репетиторов и проведения занятий. Бэкенд на FastAPI с модульным монолитом.

## Стек

- **Backend:** Python 3.12+, FastAPI, Dishka, SQLAlchemy 2.0 (async), Pydantic v2, PostgreSQL, Alembic
- **Tooling:** poetry, ruff, ty / mypy, pytest + pytest-asyncio
- **PK:** Uuid (`sqlalchemy.Uuid`, `default=uuid4`), не int.

## Структура

```
backend/app/
├── core/
│   ├── {config,db,ports,providers,unit_of_work}.py
│   └── domain/exceptions.py
├── bootstrap/
│   ├── providers/<module>.py
│   ├── container.py
│   ├── http/{app,error_handlers}.py
│   └── orm_registry.py
├── modules/<name>/{domain,application,infrastructure,presentation,public.py}
└── main.py
```

## Где что лежит

- Порты (Protocol) — `application/interfaces/`
- Реализации — `infrastructure/`
- Связка порт → реализация — `bootstrap/providers/<module>.py`
- Сборка контейнера — `bootstrap/container.py`
- HTTP entry point — `bootstrap/http/app.py`
- Модели для Alembic — `bootstrap/orm_registry.py`

## Транзакции

- `commit` делается **в use case** через `UnitOfWork`, не в провайдере сессии.
- Провайдер сессии в Dishka **не коммитит** — только открывает сессию в `Scope.REQUEST` и закрывает её при выходе из скоупа.
- `UnitOfWork` живёт в `Scope.REQUEST` и резолвится из той же сессии, что и репозитории.
- Это осознанное отклонение от «золотого стандарта» из курсов Stepik (там `commit` в провайдере). Причина: явные границы транзакции в коде, возможность нескольких коммитов на запрос, простая подмена `UnitOfWork` в тестах.

## Тестирование

- `domain` — юнит-тесты без моков
- `application` — use cases на фейках портов
- `infrastructure` — на реальной PostgreSQL
- `presentation` — `httpx.ASGITransport`
- Фейки, не моки. В API-тестах подмена провайдеров Dishka, не `dependency_overrides`

## Workflow

- Перед коммитом: `ruff format`, `ruff check --fix`, тесты
- Миграции: `alembic revision --autogenerate`, `alembic upgrade head`
- Новая модель → импорт в `bootstrap/orm_registry.py`
- Новый модуль → провайдер в `bootstrap/providers/<module>.py` + регистрация в `bootstrap/container.py`

## Работа с документацией

У меня есть инструменты `docs_search`, `fetch_url_content`, `search_web`. Использовать **обязательно** перед написанием нетривиального кода — память врёт, версии меняются.

### Когда идти в документацию

| Тема                  | Инструмент    | Что искать                                                                                      |
| --------------------- | ------------- | ----------------------------------------------------------------------------------------------- |
| Dishka                | `docs_search` | `dishka provider`, `dishka scope`, `dishka fastapi setup`, `dishka FromDishka`, `dishka taskiq` |
| SQLAlchemy async      | `docs_search` | `sqlalchemy async session`, `sqlalchemy selectinload`, `sqlalchemy bulk insert`                 |
| SQLAlchemy 2.0 модели | `docs_search` | `sqlalchemy Mapped mapped_column`                                                               |
| Alembic async         | `docs_search` | `alembic async env.py`, `run_sync`                                                              |
| FastAPI нестандартное | `docs_search` | `fastapi sse`, `fastapi websocket`, `fastapi background task`                                   |

### Что обязательно сверить

- Dishka: синтаксис `@provide`, `Scope`, `FromDishka`, `setup_dishka`, финализаторы. **Каждый раз**, потому что библиотека активно меняется.
- SQLAlchemy: bulk-операции (`insert().values()` vs `bindparam`), `on_conflict_do_update`, оконные функции.
- Alembic: шаблон `env.py` для async.
- FastAPI: SSE, `app.frontend()`, `EventSourceResponse` — это относительно новые фичи.

### Базовые URL (для `fetch_url_content`)

- FastAPI — https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 — https://docs.sqlalchemy.org/en/20/
- SQLAlchemy async — https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic — https://alembic.sqlalchemy.org/
- Pydantic v2 — https://docs.pydantic.dev/latest/
- Dishka (docs в репо) — https://github.com/reagento/dishka/tree/develop/docs

## Dishka — обязательные правила

### @inject или DishkaRoute

`FromDishka[T]` работает только если на роутере указан `route_class=DishkaRoute`, либо на каждом хендлере стоит `@inject`. Используем `DishkaRoute` на роутере — это автоматически включает инъекцию для всех хендлеров.

### Никаких «голых» типов

Нельзя регистрировать `str`, `int`, `dict`, `list` как зависимости напрямую. Если в приложении несколько строк (DSN, API-ключ, путь), контейнер не различит их.

Правильно:

```python
from typing import NewType

DatabaseDSN = NewType("DatabaseDSN", str)
ApiKey = NewType("ApiKey", str)
```

Альтернатива — dataclass-обёртки (`@dataclass(frozen=True, slots=True) class DatabaseDSN: value: str`).

### from_context — для данных извне

Объекты, созданные вне контейнера (текущий пользователь из JWT, данные запроса), передаются через `from_context`:

```python
# Провайдер
current_user = from_context(provides=CurrentUser, scope=Scope.REQUEST)

# Точка входа
async with container(context={CurrentUser: user}) as req:
    ...
```

Ключи в context — «сырые» типы, без `Annotated`. Пока auth нет — не используем, но помнить.

### ValidationSettings в тестах и CI

При создании контейнера в тестах/CI использовать:

```python
from dishka import ValidationSettings

settings = ValidationSettings(
    implicit_override=True,
    nothing_overridden=True,
    nothing_decorated=True,
)
container = make_async_container(*provider, validation_settings=settings)
```

Ловит ошибки конфигурации контейнера на старте, а не в рантайме.

### Воркеры — REQUEST-scope на задачу

Каждая задача воркера — новый REQUEST-scope. Не держать одну сессию на весь воркер:

```python
from app.bootstrap.container import create_container

container = create_container()
async with container() as request_container:
    worker = await request_container.get(Worker)
    await worker.run()
await container.close()
```

## Тестирование — нюансы

- `pythonpath = ["."]` в `pyproject.toml` — иначе pytest не видит `app`.
- `asyncio_mode = "auto"` — не писать `@pytest.mark.asyncio`.
- `DATABASE_URL` через `os.environ.setdefault(...)` **до** импорта `app`. В `conftest.py` — `# ruff: noqa: I001`.
- Dishka в тестах: `create_app(container=None)` — опциональный параметр. Тест передаёт контейнер с фейками.
- Фейковые репозитории — `Scope.APP`, не `REQUEST`. Иначе данные не переживают HTTP-запросы.
- Фейки вместо моков. `FakeAccountRepository.add` имитирует UNIQUE через `raise EmailAlreadyTakenError`.
- `FrozenInstanceError` (не `Exception`) — для тестов иммутабельности.
- Идемпотентность через `is` на `updated_at`.

## Auth

- JWT HS256, access 15 минут, refresh 30 дней.
- Refresh хранится в БД (`refresh_tokens`) как sha256-хеш, ротация при `/auth/refresh`.
- Access в payload: sub, type, jti, iat, exp. Роли нет — она тянется из users.public.
- Login/refresh/logout — use cases в modules/auth/application/use_cases/.
- CurrentUser — Depends-функция в modules/auth/presentation/dependencies.py.

Точная схема — по доке TaskIQ/arq интеграции.
