---
name: sqlalchemy-2-async
description: Правила для работы с SQLAlchemy 2.0 в async-режиме на FastAPI с DI через Dishka. Используй при написании моделей, запросов, репозиториев, миграций и настройке сессий. Скилл фиксирует современный синтаксис (select(), Mapped[], selectinload) и запрещает устаревшие паттерны (session.query, lazy="select", cascade="all, delete-orphan").
---

# SQLAlchemy 2.0 async: правила и паттерны

Современный синтаксис **SQLAlchemy 2.0** в async-режиме в связке с Dishka. 2.0 сломал совместимость с 1.x: старые примеры либо не работают, либо падают с `MissingGreenlet` в async. Применяется при написании моделей, запросов, репозиториев, настройке `async_sessionmaker` и Alembic, ревью и отладке (`MissingGreenlet`, N+1, каскады). Правила не зависят от предметной области (кроме заметок про PostgreSQL / SQLite).

## Ключевые принципы

1. **Только 2.0-синтаксис.** `select()`, `Mapped[]`, `mapped_column()`, `selectinload()`. Всё из 1.x — запрещено.
2. **`expire_on_commit=False` — обязательно.** Иначе после `commit()` любой доступ к атрибуту даст `MissingGreenlet`.
3. **`await` — только перед async-методами.**
4. **Связи грузятся явно.** `lazy="select"` запрещён. Используй `selectinload`, `joinedload`, `raise_on_sql`.
5. **Каскады — на стороне БД.** `ondelete="CASCADE"` + `passive_deletes=True`, а не `cascade="all, delete-orphan"`.
6. **Пагинация — только с `order_by()`.**
7. **Значения в SQL — только через параметры.** Никаких f-строк.
8. **Bulk — отдельный режим.** Не идёт через Unit of Work, события не срабатывают.
9. **Сессия — только через провайдер Dishka.** `get_session()` как FastAPI-зависимость не создаётся.

---

## 1. Async-сессия

### Фабрика сессий

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # обязательно, иначе MissingGreenlet после commit
    autoflush=False,
)
```

- `expire_on_commit=False` — обязательно: иначе после `commit()` обращение к атрибуту вызовет ленивую загрузку → `MissingGreenlet`.
- `class_=AsyncSession` — явно, для типизации.
- `pool_pre_ping=True` — защита от «протухших» соединений.

### Где создаётся сессия

Сессия создаётся **в провайдере Dishka** в `Scope.REQUEST`, а не через FastAPI-зависимость.

```python
# core/providers.py
from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class CoreProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return AsyncSessionLocal

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session  # commit НЕ здесь — его делает use case через UnitOfWork
```

- `SessionFactory` — `Scope.APP`, создаётся один раз.
- `AsyncSession`, `UnitOfWork`, репозитории — `Scope.REQUEST`, живут один HTTP-запрос или одну задачу воркера и получают **одну и ту же** сессию.
- Синтаксис `@provide` и `Scope` — сверить с документацией Dishka (`docs_search`).

### `await` — где можно, где нельзя

**Можно `await` перед:** `session.execute/scalars/scalar/stream/stream_scalars/commit/flush/rollback/refresh/close/delete/run_sync(...)`, `engine.dispose()`.

**Нельзя `await` перед:** `session.add(...)`, `session.add_all(...)`, построением запроса (`select(...).where/join/options/execution_options(...)`), `result.all()/first()/scalars()` — результат уже в памяти.

### Стриминг

```python
async for user in await session.stream_scalars(select(User).where(...)):
    ...
async for row in await session.stream(select(User.id, User.email)):
    ...
```

**Правило:** `stream_results=True` + `execute()` — не использовать. Только `stream()` / `stream_scalars()`.

### Обработка `IntegrityError`

```python
try:
    await session.flush()
except IntegrityError as exc:
    await session.rollback()   # обязательно
    raise EmailAlreadyTakenError(...) from exc
```

**Правило:** после `IntegrityError` — **обязательно** `await session.rollback()`, иначе сессия сломана и следующий запрос упадёт.

---

## 2. Загрузка связей

| Стратегия                | Для чего                                  |
| ------------------------ | ----------------------------------------- |
| `selectinload()`         | Коллекции (`one-to-many`, `many-to-many`) |
| `joinedload()`           | Скаляры (`many-to-one`, `one-to-one`)     |
| `contains_eager()`       | Если в запросе уже есть `join()`          |
| `with_loader_criteria()` | Фильтр внутри загрузки                    |

```python
from sqlalchemy.orm import selectinload, joinedload

stmt = select(User).options(selectinload(User.orders))       # коллекция
stmt = select(Order).options(joinedload(Order.customer))     # скаляр
```

**Правила:**

- **В async запрещено:** `lazy="select"` (по умолчанию) — обращение к такой связи без явной загрузки даст `MissingGreenlet`.
- Правильно: `lazy="selectin"` (коллекции), `lazy="joined"` (скаляры), `lazy="raise_on_sql"` (защита от N+1).
- `raiseload("*")` в `.options()` — любая незагруженная связь → ошибка:

```python
stmt = select(User).options(selectinload(User.orders), raiseload("*"))
```

- `awaitable_attrs` — только для динамических случаев, где `selectinload` неприменим. По умолчанию не использовать.

## 3. Каскады в async

**Запрещено:**

```python
orders = relationship("Order", cascade="all, delete-orphan")  # требует загрузки детей → MissingGreenlet
```

**Правильно:**

```python
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Uuid


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer",
        passive_deletes=True,   # ← обязательно
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),   # ← каскад в БД
        index=True,
    )
    customer: Mapped["Customer"] = relationship(back_populates="orders")
```

**Правила:**

- `ondelete="CASCADE"` на `ForeignKey` — удаление делает БД; `passive_deletes=True` — ORM не грузит детей сама.
- `passive_deletes=True` срабатывает только для **незагруженных** детей.
- Каскады — на стороне коллекции (`Customer.orders`), не на скаляре.

## 4. Модели

### Синтаксис 2.0

```python
from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    bio: Mapped[str | None]
```

**Правила:**

- `nullable=False` / `nullable=True` не писать — выводится из `Mapped[T]` / `Mapped[T | None]`.
- `index=True` на FK — оставить.
- `relationship(back_populates="...")` — только так; `backref` не использовать.
- `uselist=False` не указывать при `Mapped[Child]` — выводится.
- `comment="..."` — SQL-комментарий в DDL; `doc="..."` — только Python-документация.

### Primary Key — Uuid

Для всех таблиц PK — `Uuid` из `sqlalchemy`, не `int`:

```python
from uuid import UUID, uuid4

from sqlalchemy import Uuid

id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
```

- `default=uuid4` — функция без вызова, SQLAlchemy вызовет её сама.
- `nullable=False` не указывать — выводится из `Mapped[UUID]`.
- `sqlalchemy.Uuid` — `as_uuid=True` по умолчанию. `postgresql.UUID` — легаси (`as_uuid=False` по умолчанию, нужно указывать явно), не использовать.

## 5. SELECT

```python
from sqlalchemy import select

stmt = select(User).where(User.email == email)   # 2.0 — правильно
stmt = session.query(User).filter(...)           # 1.x — запрещено
```

**Правила:**

- `select()` — не `session.query()`; `.where()` — не `.filter()`.
- Пагинация — `order_by()` + `limit()` + `offset()`. Без `order_by` пагинация нестабильна.
- Keyset pagination — `where(id > last_seen_id)`.
- Фильтрация по связи — `select(User).join(User.orders).where(Order.status == "paid")`.
- Агрегаты: `func.count()` — `COUNT(*)`; `func.count(col)` — без NULL; `func.count(distinct(col))` — уникальные. `GROUP BY` — только если в SELECT есть неагрегированные колонки; `HAVING` — для агрегатов, `WHERE` — для строк.
- Оконные функции — через `.over()` (`rank`, `dense_rank`, `row_number`); фильтровать по ним — через подзапрос/CTE, в `WHERE` напрямую нельзя.

## 6. Bulk-операции

| Объём         | Инструмент                  |
| ------------- | --------------------------- |
| до ~500 строк | `insert().values([...])`    |
| от 1000 строк | `bindparam` + `executemany` |

```python
# небольшой объём
stmt = insert(User).values([{"email": e} for e in emails])
await session.execute(stmt)

# большой объём
stmt = insert(User).values({"email": bindparam("email")}).execution_options(...)
await session.execute(stmt, [{"email": e} for e in emails])
```

- `RETURNING`, `on_conflict_do_update()` / `on_conflict_do_nothing()` — PostgreSQL, SQLite.
- `bulk_save_objects()` — **устарел**, не использовать.
- Bulk **не использует** Unit of Work: события (`before_insert`, `after_insert`) не срабатывают, `session.new/dirty/deleted` пусты. `commit` после bulk делает use case вручную.

## 7. Raw SQL

```python
from sqlalchemy import text, bindparam

stmt = text("SELECT * FROM users WHERE email = :email")
result = await session.execute(stmt, {"email": email})
```

- `text()` — только именованные параметры `:name`; позиционные (`%s`, `?`) не работают.
- `bindparam(expanding=True)` — для `IN :names`.
- `from_statement()` — для ORM-объектов из сырого SQL.
- **Значения — никогда через f-строки.** Имена колонок/таблиц/направление сортировки — через белый список.

```python
stmt = text("SELECT * FROM users WHERE id IN :ids").bindparams(bindparam("ids", expanding=True))
await session.execute(stmt, {"ids": [1, 2, 3]})
```

---

## 8. Core

- `MetaData(bind=engine)` — **удалено**. Передавать `engine` в методы.
- `autoload=True` — **удалено**. Использовать `autoload_with=engine`.
- `Base.metadata` — тот же `MetaData`, что и в Core.
- `create_all()` **не обновляет** существующие таблицы. Изменения — через Alembic.

---

## 9. Alembic + async

### Что запрещено

```python
# TypeError: синхронный Connection не поддерживает async-контекст
async with engine.sync_engine.connect() as conn:
    ...
```

`engine.sync_engine` — только цель для `@event.listens_for`. **Не источник соединений.**

### Правильно

```python
# engine.connect() — метод AsyncEngine
async with engine.connect() as conn:
    await conn.run_sync(do_run_migrations)
```

### Правила

- `run_sync()` — единственный способ выполнить синхронный Alembic в async.
- `config.set_main_option("sqlalchemy.url", ...)` не нужен, если используешь `engine` приложения — URL уже внутри движка.
- В `env.py` — `from app.bootstrap import orm_registry  # noqa: F401` **обязательно** (иначе `--autogenerate` не увидит модели).
- `dispose()`: движок приложения закрывается в `lifespan`/финализаторе `APP`-провайдера, отдельный движок Alembic — своим кодом (см. раздел 10).

---

## 10. Интеграция с Dishka и FastAPI

- Сессия — в провайдере Dishka в `Scope.REQUEST` (см. раздел 1), `SessionFactory` — в `Scope.APP`.
- `UnitOfWork` — тоже `Scope.REQUEST` и получает **ту же** сессию, что и репозитории:

```python
# core/providers.py
@provide(scope=Scope.REQUEST)
def provide_uow(self, session: AsyncSession) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(session=session)
```

Это гарантирует, что `flush` в репозитории и `commit` в use case работают в одной транзакции.

- Роутеры используют `route_class=DishkaRoute` на `APIRouter` — иначе `FromDishka[T]` не активирует инъекцию. Никакого `Depends` для бизнес-зависимостей (пример роутера — в скилле `fastapi-clean-architecture`).
- `Depends` остаётся только для FastAPI-native вещей: `OAuth2PasswordBearer`, `HTTPBearer`, `APIKeyHeader` из `fastapi.security`.
- `dispose()` движка приложения — в `lifespan` после `yield`:

```python
# bootstrap/http/app.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
```

Для воркеров / CLI / планировщиков `dispose()` вызывается либо в финализаторе `APP`-провайдера (`provide_engine` через `yield` + `finally: await engine.dispose()`), либо вручную в entry point после `container.close()`.

---

## 11. Работа с документацией

**Правило: перед написанием нетривиального кода с SQLAlchemy 2.0 агент обязан сверить актуальный API через инструменты поиска по документации.**

SQLAlchemy 2.0 продолжает развиваться. Async-расширение, bulk-операции, Alembic-интеграция — всё это имеет нюансы, которые лучше проверять по документации, а не по памяти.

### Инструменты для сверки

- **`docs_search`** — основной инструмент. Искать по ключевым словам: `sqlalchemy async session`, `sqlalchemy selectinload`, `sqlalchemy Mapped mapped_column`, `sqlalchemy bulk insert`, `alembic async`.
- **`fetch_url_content`** — открыть конкретную страницу, если `docs_search` не дал точного ответа.
- **`search_web`** — если нужно найти нестандартный пример, issue или обсуждение.

### Куда идти в первую очередь

| Что проверить                                               | Раздел документации                                                   |
| ----------------------------------------------------------- | --------------------------------------------------------------------- |
| Async ORM, `AsyncSession`, `async_sessionmaker`             | `https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html`       |
| Загрузка связей (`selectinload`, `joinedload`, `raiseload`) | `https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html` |
| SELECT, фильтры, агрегаты                                   | `https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html`        |
| Bulk / DML (`insert().values`, `bindparam`)                 | `https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html`           |
| Модели 2.0 (`Mapped`, `mapped_column`)                      | `https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html`       |
| Core (Connection, Engine, MetaData)                         | `https://docs.sqlalchemy.org/en/20/core/`                             |
| Alembic + async                                             | `https://alembic.sqlalchemy.org/en/latest/cookbook.html`              |

### Что обязательно сверить

`async_sessionmaker` (аргументы `class_`, `expire_on_commit`); синтаксис `select()`, `.options()`, `.join()`; вложение `selectinload` / `joinedload`; bulk DML (`insert().values([...])` vs `bindparam` + `executemany`); `on_conflict_do_update` / `on_conflict_do_nothing` для PostgreSQL / SQLite; шаблон async Alembic (`env.py`, `run_sync`, `do_run_migrations`); оконные функции (`.over()`) в подзапросах.

### Что делать при расхождении

**Порядок приоритетов:** документация библиотеки → `.kodarules` → скиллы → `KODA.md`.

1. **Верь документации.** Скилл фиксирует паттерны; документация описывает текущий API.
2. **Не копируй код из скилла слепо.** Особенно строки с `async_sessionmaker`, `select().options(...)`, `insert().values(...)`, `run_sync(...)`.
3. **Обнови скилл**, если изменился не API, а паттерн.

### Что остаётся верным независимо от версии SQLAlchemy 2.x

- `expire_on_commit=False` — обязательно.
- `select()` вместо `session.query()`; `Mapped[]` + `mapped_column()` вместо `Column()`.
- `lazy="select"` запрещён в async.
- `cascade="all, delete-orphan"` запрещён; вместо него `ondelete="CASCADE"` + `passive_deletes=True`.
- `await` только перед async-методами; значения в SQL — только через параметры.
- `passive_deletes=True` не работает для загруженных детей.
- Bulk не идёт через Unit of Work.
- Сессия — только через провайдер Dishka; `get_session()` не создаётся.

---

## Чек-лист

**Сессия и транзакции**

- [ ] `expire_on_commit=False` и `class_=AsyncSession` в `async_sessionmaker`.
- [ ] `await` только перед async-методами; после `IntegrityError` — `await session.rollback()`.
- [ ] `stream_scalars` / `stream` вместо `stream_results=True` + `execute()`.
- [ ] Сессия — в провайдере Dishka (`Scope.REQUEST`), `SessionFactory` — `Scope.APP`; `get_session()` не создаётся.
- [ ] Провайдер сессии не вызывает `commit`; `commit` делает use case через `UnitOfWork`.

**Связи и каскады**

- [ ] `selectinload` для коллекций, `joinedload` для скаляров, `contains_eager` при явном `join`.
- [ ] `lazy="select"` не используется; `raiseload("*")` в `.options()` для защиты от N+1.
- [ ] `awaitable_attrs` только в крайнем случае.
- [ ] `ondelete="CASCADE"` на `ForeignKey`, `passive_deletes=True` на `relationship()`.
- [ ] `cascade="all, delete-orphan"` не используется; каскады — на стороне коллекции.

**Модели и SELECT**

- [ ] `Mapped[T]` + `mapped_column()`, не `Column()`; `nullable` не указан вручную.
- [ ] `back_populates`, не `backref`; `uselist=False` не указан; `index=True` на FK.
- [ ] PK — `Uuid` (`sqlalchemy.Uuid`, `default=uuid4`), не `int`.
- [ ] `select()` вместо `session.query()`; `.where()` вместо `.filter()`.
- [ ] Пагинация — только с `order_by()` (keyset — `where(id > last_seen_id)`).
- [ ] Оконные функции — через `.over()`, фильтрация — через подзапрос / CTE.

**Bulk, Raw SQL, Core, Alembic**

- [ ] `insert().values([...])` до ~500 строк, `bindparam` + `executemany` от 1000; `bulk_save_objects()` не используется.
- [ ] События в bulk не ожидаются.
- [ ] `text()` с именованными параметрами; `bindparam(expanding=True)` для `IN`; значения — не через f-строки.
- [ ] `autoload_with=engine`, не `autoload=True`; `MetaData(bind=engine)` не используется; схема — через Alembic.
- [ ] `engine.connect()`, не `engine.sync_engine.connect()`; `run_sync()` для синхронного Alembic.
- [ ] `from app.bootstrap import orm_registry  # noqa: F401` в `env.py`.
- [ ] `dispose()` движка приложения — в `lifespan` после `yield`; отдельного движка Alembic — в коде Alembic.

**Dishka + FastAPI**

- [ ] Сессия и UnitOfWork — в `Scope.REQUEST`, `SessionFactory` — в `Scope.APP`.
- [ ] Роутеры используют `route_class=DishkaRoute`; в эндпоинтах — `FromDishka[T]`.
- [ ] `Depends` — только для FastAPI-native вещей (`OAuth2PasswordBearer`, `HTTPBearer`, `APIKeyHeader`).

---

## Запреты

- `session.query()` и `filter()`.
- `nullable=False` при `Mapped[str]` / `nullable=True` при `Mapped[str | None]`.
- `stream_results=True` в async с `execute()`.
- `isolation_level` на `Select.execution_options()` — только на `Connection` / `Engine`.
- `engine.sync_engine.connect()` в `async with`.
- `cascade="all, delete-orphan"` в async.
- `bulk_save_objects()`.
- f-строки для значений в SQL.
- Забыть `await session.rollback()` после `IntegrityError`.
- `lazy="select"` в моделях async-проекта.
- Смешивание `Depends` и `FromDishka` для одной и той же зависимости.
- Создание сессии в обход провайдера Dishka.

---

## Что НЕ входит в эти правила

Подключается поверх по необходимости: конкретная СУБД (диалект), пул соединений, `testcontainers`, SQLModel, `alembic` naming convention, мониторинг запросов, разделение read/write моделей.

Правила из этого скилла остаются неизменными независимо от того, что из этого списка подключено.
