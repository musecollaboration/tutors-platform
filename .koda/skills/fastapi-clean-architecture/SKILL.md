---
name: fastapi-clean-architecture
description: Универсальные правила для бэкенда на FastAPI в виде модульного монолита с DI через Dishka. Используй при старте проекта, добавлении модуля, рефакторинге, проверке границ между слоями и модулями. Правила не зависят от БД и предметной области.
---

# FastAPI: универсальные правила модульной архитектуры

Инвариантная часть архитектуры FastAPI-бэкенда: не зависит от проекта, БД и предметной области. Применяется при старте проекта, добавлении модуля или точки входа, рефакторинге, проверке границ. Примеры используют нейтральные имена: модуль `users`, сущность `Account`, точки входа `http`, `worker`, `cli`, `scheduler`. `<module>`, `<name>`, `<command>`, `<job>` — подстановочные имена.

## Ключевые принципы

1. **Сначала модуль, потом слой.** Верхний уровень делится по бизнес-модулям, внутри модуля идут слои.
2. **Зависимости направлены внутрь.** `presentation` и `infrastructure` знают о `application` и `domain`, но не наоборот.
3. **Порты принадлежат `application`.** Use case определяет, что ему нужно от внешнего мира, а `infrastructure` это реализует.
4. **Модули общаются только через `public.py`.** Никаких чужих сущностей, репозиториев и таблиц.
5. **Транзакцией управляет use case**, а не репозиторий и не роутер.
6. **Доменные исключения не знают про HTTP.** Статус назначается один раз в `bootstrap`.
7. **Сущность мутабельна и имеет поведение. Value object иммутабелен.** Это разные инструменты для разных задач.
8. **DI — через Dishka, один контейнер на всё приложение.** HTTP, воркеры, CLI, планировщики используют одни и те же провайдеры. Никаких `Depends` для бизнес-зависимостей.
9. **Провайдеры модулей живут в `bootstrap/providers/`, общие провайдеры (SessionFactory, UnitOfWork, Config) — в `core/providers.py`.** Провайдер импортирует и порты, и реализации — значит, его место в composition root, а не в модуле.
10. **Перед написанием кода с Dishka — обязательная сверка с документацией.** Через `docs_search`, `fetch_url_content` или `search_web`. Примеры в этом скилле показывают паттерн, а не точный API.

---

## 1. Структура папок модуля

Каждый бизнес-модуль имеет **одинаковую структуру**. Без исключений.

```
modules/<name>/
├── domain/                  # чистая логика модуля
│   ├── entities/            # сущности с поведением
│   ├── value_objects/       # иммутабельные VO
│   └── exceptions.py        # доменные исключения
├── application/             # сценарии использования
│   ├── ports/               # порты (Protocol)
│   ├── dto/                 # read-DTO
│   └── use_cases.py         # (или use_cases/ при росте)
├── infrastructure/          # реализации
│   ├── models.py            # ORM-модели
│   ├── repositories.py      # реализации репозиториев
│   └── adapters.py          # внешние сервисы, хешеры, шлюзы
├── presentation/            # HTTP
│   ├── router.py
│   └── schemas.py
└── public.py                # контракт для других модулей
```

Общий уровень:

```
app/
├── core/                    # общее ядро
│   ├── config.py            # настройки
│   ├── db.py                # Base, engine, async_session_factory
│   ├── ports.py             # Protocol UnitOfWork (контракт)
│   ├── unit_of_work.py      # SqlAlchemyUnitOfWork (реализация)
│   ├── providers.py         # CoreProvider (импортирует SqlAlchemyUnitOfWork)
│   └── domain/exceptions.py # базовые исключения
├── bootstrap/               # composition root — см. раздел 2
├── modules/                 # бизнес-модули
└── main.py                  # HTTP entry point
```

**Правила:**

- У каждого модуля одинаковый набор папок — без исключений.
- `core` не импортирует ничего из `modules`.
- `bootstrap` знает всех, остальные знают только `core` и себя.
- Один модуль — одна бизнес-область.
- `dto/` и `ports/` — пакеты (при росте будет несколько файлов).
- `use_cases.py` — один файл, пока сценариев мало. При росте — `use_cases/`.
- **В модуле нет провайдеров Dishka и нет `dependencies.py`.**

---

## 2. Bootstrap: composition root

`bootstrap` и `core/providers.py` вместе образуют **composition root** — только здесь интерфейсы (Protocol из `application`) встречаются с реализациями (`infrastructure`). **Один Dishka-контейнер на всё приложение**: HTTP, воркеры, CLI и планировщики используют одни и те же провайдеры.

| Точка входа    | Что делает с контейнером                            | Где живёт файл              |
| -------------- | --------------------------------------------------- | --------------------------- |
| HTTP           | подключает контейнер к FastAPI через `setup_dishka` | `bootstrap/http/`           |
| Воркер очереди | создаёт контейнер и достаёт из него worker          | `bootstrap/workers/`        |
| CLI            | создаёт контейнер и достаёт из него use case        | `bootstrap/cli/`            |
| Планировщик    | создаёт контейнер и достаёт из него use case        | `bootstrap/scheduler/`      |
| Alembic        | импорт ORM-моделей всех модулей                     | `bootstrap/orm_registry.py` |

```
bootstrap/
├── providers/                # Dishka-провайдеры — ЗДЕСЬ ЖИВУТ ЗАВИСИМОСТИ
│   ├── <module>.py           # провайдер модуля
│   └── ...                   # по одному на модуль
├── http/                     # HTTP entry point
│   ├── app.py                # create_app() + setup_dishka
│   └── error_handlers.py     # DomainError → HTTP
├── workers/<name>.py         # run_<name>_worker()
├── cli/<command>.py          # run_<command>()
├── scheduler/<job>.py        # run_<job>()
├── container.py              # сборка Dishka-контейнера из всех провайдеров
└── orm_registry.py           # импорт моделей для Alembic
```

### Правила для любой точки входа

- Один entry point — один файл.
- Файл **запускает процесс**: создаёт контейнер, достаёт корневой объект, вызывает `run()` или подключает к фреймворку.
- Никакой бизнес-логики, никаких `if` по домену.
- Зависимости резолвятся **только через контейнер**. Ручное создание объектов запрещено, кроме самого контейнера.
- Bootstrap может импортировать **всё**; сам он **никем не импортируется**, кроме точек входа (`main.py`, `worker.py`, `cli.py`).

### Сборка контейнера

Контейнер собирается из провайдеров: `core` даёт общие, каждый модуль — свой, `bootstrap/container.py` объединяет.

```python
# bootstrap/container.py
from dishka import make_async_container

from app.core.providers import CoreProvider
from app.bootstrap.providers.users import UsersProvider
from app.bootstrap.providers.orders import OrdersProvider


def create_container():
    return make_async_container(
        CoreProvider(),
        UsersProvider(),
        OrdersProvider(),
    )
```

Скоупы:

| Scope     | Что в нём живёт                                             |
| --------- | ----------------------------------------------------------- |
| `APP`     | конфиг, engine, `SessionFactory`, адаптеры внешних сервисов |
| `REQUEST` | сессия, `UnitOfWork`, репозитории, use cases                |
| `SESSION` | для websocket-соединений, если они есть                     |
| `STEP`    | для очень гранулярных сценариев, обычно не нужен            |

**Правила:**

- Один модуль — один провайдер в `bootstrap/providers/<module>.py`.
- Провайдер импортирует и порты из `application`, и реализации из `infrastructure` — поэтому он **не может** жить в модуле.
- Провайдер описывает **только свой модуль**. Если модулю A нужны данные из B — порт в `A.ports`, реализация через `B.public` в `adapters.py` A.
- Scope — по времени жизни: конфиг и engine — `APP`, всё что работает с транзакцией — `REQUEST`.
- Синглтонов и глобального состояния вне `APP` быть не должно.

### Точки входа

HTTP подключает контейнер через `setup_dishka`; эндпоинты получают зависимости через `FromDishka[T]`.

```python
# bootstrap/http/app.py
from app.bootstrap.container import create_container


def create_app() -> FastAPI:
    container = create_container()
    app = FastAPI()
    setup_dishka(container, app)
    register_error_handlers(app)
    app.include_router(users_router, prefix="/api/v1")
    return app
```

Для async-проектов контейнер создаётся через `create_container()`, который внутри вызывает `make_async_container()`. Синхронный `make_container()` из Dishka не поддерживает `await container.get(...)` и `async with container()`.

```python
# presentation/router.py
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

router = APIRouter(prefix="/accounts", tags=["accounts"], route_class=DishkaRoute)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def register_account(
    body: RegisterAccountRequest,
    use_case: FromDishka[RegisterAccount],
) -> AccountResponse:
    account = await use_case.execute(body.email, body.password)
    return AccountResponse.from_entity(account)
```

Роутер не импортирует `infrastructure` и не знает, откуда берётся `RegisterAccount` — просто просит контейнер через `FromDishka`.

Воркер / CLI / планировщик — тот же принцип: контейнер на процесс, корневой объект из контейнера, закрытие в конце.

```python
# bootstrap/workers/<name>.py
from app.bootstrap.container import create_container


async def run_<name>_worker() -> None:
    container = create_container()
    worker = await container.get(<Name>Worker)
    await worker.run()
    await container.close()
```

### orm_registry для Alembic

```python
# bootstrap/orm_registry.py
from app.modules.users.infrastructure import models as users_models      # noqa: F401
from app.modules.orders.infrastructure import models as orders_models    # noqa: F401
# при добавлении модуля дописывай импорт его моделей здесь
```

В `migrations/env.py` импортируется `app.bootstrap.orm_registry`, а `target_metadata = Base.metadata`.

### Чего в bootstrap быть не должно

- Бизнес-правил, валидации, `if`-ов по домену.
- Ручного создания объектов, кроме самого контейнера.
- `Depends` для бизнес-зависимостей — только `FromDishka`.
- Импортов из `bootstrap` в `domain`, `application`, `infrastructure`, `presentation`.
- Глобального состояния, живущего дольше контейнера.
- Логики, которая должна быть в use case.

### HTTP vs остальные точки входа

HTTP подключает контейнер через `setup_dishka` и отдаёт зависимости через `FromDishka[T]`; маппинг `DomainError → HTTP` — часть HTTP-точки входа, а не общая часть для всех. Воркер / CLI / планировщик достают корневой объект через `container.get(...)` при старте процесса, слоя `presentation` у них нет, и `DomainError` они обрабатывают сами (логируют, решают retry).

### Пример провайдера

Ниже — **архитектурный паттерн**, а не точный API. Сверь синтаксис с документацией Dishka (раздел 9).

```python
# bootstrap/providers/users.py
from dishka import Provider, Scope, provide

from app.modules.users.application.ports.account_repository import AccountRepository
from app.modules.users.application.ports.password_hasher import PasswordHasher
from app.modules.users.application.use_cases import RegisterAccount
from app.modules.users.infrastructure.repositories import SqlAlchemyAccountRepository
from app.modules.users.infrastructure.adapters import BcryptPasswordHasher


class UsersProvider(Provider):
    scope = Scope.REQUEST

    account_repository = provide(SqlAlchemyAccountRepository, provides=AccountRepository)
    password_hasher = provide(BcryptPasswordHasher, provides=PasswordHasher)
    register_account = provide(RegisterAccount)
```

### Где живут зависимости

Зависимости описываются **не функциями, а Dishka-провайдерами**. Провайдер обязан импортировать и порты из `application`, и реализации из `infrastructure` — это разрешено только `bootstrap`, поэтому провайдеры модулей не могут жить в модулях. Из модуля удаляются `presentation/dependencies.py`, `presentation/provider.py` и любые функции `build_*` — их место в `bootstrap`. Заглушки `get_*` заменены на `FromDishka[T]`.

---

## 3. Правила импортов

Направление зависимостей:

```
presentation ─┐
              ├──> application ──> domain
infrastructure┘

bootstrap ──> знает всех
core      <── знают все, core не знает никого
```

| Слой             | Может импортировать                              | Не может импортировать                                                                          |
| ---------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `domain`         | stdlib, `core.domain`                            | FastAPI, SQLAlchemy, Pydantic, Dishka, application, infrastructure, presentation, другие модули |
| `application`    | `domain`, `core`, stdlib                         | infrastructure, presentation, FastAPI, SQLAlchemy, Dishka                                       |
| `infrastructure` | `application`, `domain`, `core`, библиотеки      | presentation                                                                                    |
| `presentation`   | `application`, `domain`, `core`, FastAPI, Dishka | infrastructure                                                                                  |
| `bootstrap`      | всех                                             | —                                                                                               |
| `core`           | stdlib, Dishka                                   | `modules`, `bootstrap`                                                                          |

**Правила:**

- `domain` не знает про БД, HTTP, фреймворк и DI-контейнер.
- `application` не знает, чем именно реализованы порты, и не знает про Dishka.
- `presentation` не импортирует `infrastructure`. Зависимости приходят через `FromDishka`.
- Между модулями — только `public.py`.
- `core` не импортирует `modules`. Dishka в `core` допустима — там живут общие провайдеры.
- `bootstrap` и `core/providers.py` вместе образуют composition root — только здесь сходятся интерфейсы и реализации. Провайдеры модулей живут в `bootstrap/providers/<module>.py`, общие провайдеры (SessionFactory, UnitOfWork, Config) — в `core/providers.py`.
- `bootstrap` не импортируется никем, кроме точек входа (`main.py`, воркеры, CLI, планировщики).

---

## 4. Правила домена

### Сущность — мутабельна, с поведением

Сущность — объект с жизненным циклом и инвариантами. У неё есть идентичность (`id`), которая сохраняется при изменении состояния. Сущность мутабельна: методы меняют её состояние, а не возвращают новый объект.

```python
# domain/entities/account.py
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

from app.modules.users.domain.value_objects.email import Email


@dataclass(slots=True, eq=False)
class Account:
    """Authentication credentials linked to a user. Tracks lock status."""

    _id: UUID
    _user_id: UUID
    _email: Email
    _password_hash: str
    _created_at: datetime
    _updated_at: datetime | None = None
    _is_locked: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Account):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    @classmethod
    def create(cls, user_id: UUID, email: Email, password_hash: str) -> Self:
        return cls(
            _id=uuid4(),
            _user_id=user_id,
            _email=email,
            _password_hash=password_hash,
            _created_at=datetime.now(UTC),
            _is_locked=False,
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def email(self) -> Email:
        return self._email

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def is_locked(self) -> bool:
        return self._is_locked

    def change_password(self, password_hash: str) -> None:
        self._password_hash = password_hash
        self._updated_at = datetime.now(UTC)

    def lock(self) -> None:
        if self._is_locked:
            return
        self._is_locked = True
        self._updated_at = datetime.now(UTC)

    def unlock(self) -> None:
        if not self._is_locked:
            return
        self._is_locked = False
        self._updated_at = datetime.now(UTC)
```

**Правила:**

- У сущности есть методы-действия (`lock`, `unlock`, `change_password`), а не только поля; инварианты проверяются в методах.
- **Все доменные методы идемпотентны.** Повторный `lock()` не бросает исключение и не трогает `_updated_at`. Если состояние уже такое, каким должно стать — `return`.
- Стиль полей: `_name` + `@property` для публичного чтения. Прямые сеттеры запрещены.
- `@dataclass(slots=True, eq=False)` + свои `__eq__` и `__hash__` по `_id`. Иначе dataclass генерирует `__eq__` по всем полям и обнуляет `__hash__`.
- PK сущности — `UUID`, не `int`.
- `_id: UUID` без `| None`, потому что `create()` генерирует id в домене. Если id генерируется БД — тогда `UUID | None`.
- Никаких `async` методов и сеттеров (`set_locked`) — только осмысленные действия.
- `datetime.now(UTC)` — всегда с таймзоной.
- Сущность не знает про другие агрегаты; связи — через ID.
- Анемичная сущность (только поля) — ошибка.
- Сообщения доменных исключений — **на английском**. Русский — только в presentation.

### Value Object — иммутабелен, по значению

Value object определяется значением, а не идентичностью. Два `Email("a@b.com")` — один и тот же объект. Он не меняется: чтобы получить другой email, создаётся новый VO.

```python
# domain/value_objects/email.py
from dataclasses import dataclass

from app.modules.users.domain.exceptions import InvalidEmailError


@dataclass(frozen=True, slots=True)
class Email:
    """Email address. Normalized on creation, immutable afterwards."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if "@" not in normalized or len(normalized) > 255:
            raise InvalidEmailError(f"Invalid email: {self.value!r}")
        object.__setattr__(self, "value", normalized)
```

**Правила:**

- `frozen=True`, `slots=True`; валидация в `__post_init__`; нормализация через `object.__setattr__`.
- Равенство по значению даёт dataclass; `id` у VO нет.
- VO создаётся, только если правило используется больше одного раза. Кандидаты: `Email`, `Money`, `PhoneNumber`, `DateRange`.
- Сообщения исключений — на английском.

### Доменные исключения

```python
# domain/exceptions.py
from app.core.domain.exceptions import AlreadyExistsError, DomainError, NotFoundError


class AccountNotFoundError(NotFoundError): ...
class EmailAlreadyTakenError(AlreadyExistsError): ...
class AccountAlreadyLockedError(DomainError): ...
class InvalidEmailError(DomainError): ...
```

**Правила:**

- Наследуются от базовых в `core.domain.exceptions` — глобальный обработчик сам подберёт статус.
- Имя отражает бизнес-смысл (`EmailAlreadyTakenError`), а не технику.
- Сообщение — на английском, без стектрейсов и SQL.
- Никаких `HTTPException` — HTTP не дело домена.
- Если метод идемпотентный — исключение для «уже в таком состоянии» не нужно. Исключения — только для настоящих нарушений инвариантов.

### Что домен НЕ делает

- Не импортирует `fastapi`, `sqlalchemy`, `pydantic`, `dishka`, HTTP-клиенты.
- Не знает про транзакции, `commit`, сессии.
- Не обращается к другим модулям, не логирует, не бросает `HTTPException`.

### Язык кода и документации

**Английский:**

- Имена классов, функций, переменных, модулей.
- Docstrings — императив, точка в конце (`"""Convert UserModel to User entity."""`).
- Сообщения доменных исключений (`raise InvalidEmailError(f"Invalid email: {self.value!r}")`).
- Логи (`logger.info("User registered", extra={...})`).

**Русский:**

- Комментарии в коде (`# Пробел не допускается внутри email`).
- OpenAPI-описания в Pydantic-схемах (`Field(description="Email пользователя")`).
- Тексты эндпоинтов для Swagger (`summary`, `description` у `@router.post(...)`).
- Пользовательские сообщения в `bootstrap/http/error_handlers.py` (маппинг `DomainError → detail`).
- Тексты писем, уведомлений, push-сообщений.

**Правило простое:** английский — всё, что видит разработчик (код, логи, IDE, тесты). Русский — всё,
что видит пользователь (Swagger, ошибки в HTTP-ответах, письма) и комментарии для команды.

---

## 5. Транзакции

**Правило: `flush` в репозитории, `commit` в use case.**

Транзакция — граница бизнес-операции, а не работы с БД. Поэтому она открывается и закрывается на уровне use case.

```python
# infrastructure/repositories.py — только flush
from sqlalchemy.exc import IntegrityError


class SqlAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, account: Account) -> Account:
        model = AccountModel(
            id=account.id,
            user_id=account.user_id,
            email=account.email.value,
            password_hash=account._password_hash,
            created_at=account.created_at,
            is_locked=account.is_locked,
        )
        self._session.add(model)
        try:
            await self._session.flush()  # flush, а не commit
        except IntegrityError as exc:
            await self._session.rollback()  # обязательно
            raise EmailAlreadyTakenError(f"Email {account.email.value} is already taken") from exc
        return _to_entity(model)
```

```python
# application/use_cases.py — commit через UoW
from dataclasses import dataclass

from app.core.ports import UnitOfWork
from app.modules.users.application.ports.account_repository import AccountRepository
from app.modules.users.application.ports.password_hasher import PasswordHasher
from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.exceptions import EmailAlreadyTakenError
from app.modules.users.domain.value_objects.email import Email


@dataclass(slots=True)
class RegisterAccount:
    accounts: AccountRepository
    hasher: PasswordHasher
    uow: UnitOfWork

    async def execute(self, user_id: UUID, email: Email, password: str) -> Account:
        if await self.accounts.get_by_email(email):
            raise EmailAlreadyTakenError(f"Email {email.value} is already taken")

        account = Account.create(user_id, email, self.hasher.hash(password))
        account = await self.accounts.add(account)
        await self.uow.commit()
        return account
```

**Правила:**

- Репозиторий никогда не вызывает `commit`; `commit` делает use case через `UnitOfWork`.
- Репозиторий и UoW одного запроса работают с одной сессией — оба резолвятся в `Scope.REQUEST`.
- Один запрос — одна транзакция (по умолчанию).
- Уникальность защищается `UNIQUE`-констрейнтом в БД, а не только проверкой в use case.
- `IntegrityError` переводится в доменное исключение **в репозитории**.
- Проверка в use case — fast-path и понятное сообщение, но **не** защита от гонки (TOCTOU): защищает только `UNIQUE` + `IntegrityError`.
- Для воркера `REQUEST`-scope создаётся на одну задачу: одна задача — одна транзакция.
- **Use case — обычный класс, зависимости в `__init__`, единственный публичный метод `async execute(...)`.** Никаких `__call__`.

---

## 6. Обработка ошибок

**Правило: доменные исключения → глобальный маппинг в HTTP.**

```python
# bootstrap/http/error_handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.domain.exceptions import (
    AlreadyExistsError,
    DomainError,
    InvalidDataError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitExceededError,
    UnauthorizedError,
)

# Порядок важен: от частных к общим
_STATUS_MAP: list[tuple[type[DomainError], int]] = [
    (UnauthorizedError, 401),
    (RateLimitExceededError, 429),
    (NotFoundError, 404),
    (AlreadyExistsError, 409),
    (PermissionDeniedError, 403),
    (InvalidDataError, 422),
    (DomainError, 400),
]


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status = next(code for cls, code in _STATUS_MAP if isinstance(exc, cls))
        return JSONResponse(status_code=status, content={"detail": str(exc)})
```

**Правила:**

- Домен бросает только доменные исключения; HTTP-статус назначается в **одном** месте.
- В роутерах нет `try/except`; в домене нет `HTTPException`.
- Обработчик регистрируется один раз в `bootstrap`.
- **Двухуровневая иерархия: `core` — категории (статусы), модули — конкретика.** `_STATUS_MAP` ссылается только на `core.domain.exceptions`; bootstrap не импортирует исключения модулей.
- Порядок в `_STATUS_MAP` — от частных к общим (`isinstance` идёт сверху вниз).
- Маппинг в HTTP — только для HTTP-точки входа. Воркеры, CLI и планировщики обрабатывают `DomainError` **сами**: логируют и решают, повторять или нет.

Пример роутера:

```python
# presentation/router.py
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status


router = APIRouter(prefix="/accounts", tags=["accounts"], route_class=DishkaRoute)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def register_account(
    body: RegisterAccountRequest,
    use_case: FromDishka[RegisterAccount],
) -> AccountResponse:
    account = await use_case.execute(body.email, body.password)
    return AccountResponse.from_entity(account)
```

Роутер только принимает запрос, вызывает use case через `use_case.execute(...)` и формирует ответ. Если use case бросит `EmailAlreadyTakenError`, глобальный обработчик превратит его в 409.

---

## 7. Порты в application

**Правило: `Protocol`, не `ABC`.**

Порт описывает, **что** нужно use case от внешнего мира. Реализация подходит по структуре — наследование не требуется.

```python
# application/ports/account_repository.py
from typing import Protocol
from uuid import UUID

from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.value_objects.email import Email


class AccountRepository(Protocol):
    async def get_by_id(self, account_id: UUID) -> Account | None: ...
    async def get_by_email(self, email: Email) -> Account | None: ...
    async def add(self, account: Account) -> Account: ...
    async def update(self, account: Account) -> None: ...
```

```python
# application/ports/password_hasher.py
from typing import Protocol


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...
```

**Правила:**

- Порты живут в `application/ports/`, не в `infrastructure`; `Protocol`, не `ABC`.
- Без префикса `I` (не `IAccountRepository`, а `AccountRepository`).
- Порт описывает, **что** нужно use case, а не **как** это сделано; возвращает сущности и VO, не ORM-модели.
- **Порты принимают VO, а не примитивы.** `get_by_email(email: Email)`, не `get_by_email(email: str)`. Валидация уже прошла в `Email.__post_init__`.
- Один порт — один контракт.
- Общие порты (например, `UnitOfWork`) — в `core/ports.py`.
- Порты для воркеров/CLI/планировщиков — там же, в `application/ports/`.
- **Привязка порта к реализации** — только в Dishka-провайдере (`bootstrap/providers/<module>.py`).

### Никаких «голых» типов

Порты и фабрики не возвращают `str`, `int`, `dict`, `list` напрямую — контейнер не различит несколько строк (DSN, API-ключ, путь). Оборачивай в NewType или dataclass:

```python
from typing import NewType

DatabaseDSN = NewType("DatabaseDSN", str)
ApiKey = NewType("ApiKey", str)
```

---

## 8. Границы между модулями

**Правило: модули общаются только через `public.py`.**

```python
# modules/users/public.py
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserSummary:
    """Публичный снимок пользователя для других модулей."""
    id: UUID
    full_name: str
    is_active: bool


class UsersFacade(Protocol):
    """Публичный интерфейс модуля users."""
    async def get_summary(self, user_id: UUID) -> UserSummary | None: ...
```

Адаптер другого модуля:

```python
# infrastructure/adapters.py модуля orders
from uuid import UUID

from app.modules.users.public import UsersFacade, UserSummary


class UsersAdapter:
    def __init__(self, facade: UsersFacade) -> None:
        self._facade = facade

    async def get_user_summary(self, user_id: UUID) -> UserSummary | None:
        return await self._facade.get_summary(user_id)
```

**Правила:**

- Импорт из другого модуля — только `app.modules.<other>.public`.
- `public.py` содержит DTO (frozen) и фасад (Protocol).
- Сущности, VO, ORM-модели наружу не отдаются; чужие таблицы не читаются и не пишутся.
- Связь между модулями — по ID, не по объектам.
- Если модулю A нужны данные из B — свой порт в `application/ports/` модуля A, реализация через `B.public` в `infrastructure/adapters.py` модуля A. Привязка — в `bootstrap/providers/<A>.py`.
- Внешние ключи между модулями — крайняя мера.
- DTO иммутабельный, потому что пересекает границу модуля: это контракт и снимок, а не объект с поведением.

**Почему в `public.py` фасад, а не прямой доступ к репозиторию:**

Модуль `orders` не может позвать `AccountRepository` из `users` — он не знает его структуру. Вместо этого `users` публикует `UsersFacade` — Protocol, описывающий **что** модуль готов предоставить другим. Реализация фасада живёт в `users`, привязка — в провайдере. Модуль `orders` видит только Protocol и DTO.

---

## 9. Работа с Dishka: сверка с документацией

**Правило: перед написанием любого кода с Dishka агент обязан сверить актуальный API через инструменты поиска по документации.** Dishka активно развивается: синтаксис декораторов, названия классов, сигнатуры интеграций могут меняться между версиями. Скилл описывает **что** должно быть, документация — **как** это пишется в текущей версии.

FastAPI-роутеры используют `route_class=DishkaRoute` — это включает автоинъекцию для `FromDishka[T]` без `@inject` на каждом хендлере. Без `DishkaRoute` `FromDishka[T]` не сработает.

**Альтернатива** — `@inject` на каждом эндпоинте. Она нужна в трёх случаях:

- `Depends`-функции (FastAPI-native auth: `OAuth2PasswordBearer`, `HTTPBearer`).
- WebSocket-эндпоинты (`DishkaRoute` работает только с HTTP).
- Чужие роутеры, куда нельзя поставить `route_class`.

**`FastapiProvider()`** — добавить в контейнер, если в провайдерах используется `Request` или `WebSocket`. Понадобится при работе с auth.

### ValidationSettings

В тестах и CI создавать контейнер со строгой валидацией:

```python
from dishka import ValidationSettings

settings = ValidationSettings(
    implicit_override=True,
    nothing_overridden=True,
    nothing_decorated=True,
)
container = make_async_container(*providers, validation_settings=settings)
```

Ловит ошибки конфигурации контейнера при старте: неявные переопределения, `override=True` без цели, `@decorate` без цели. В production можно оставить по умолчанию.

### Инструменты и что сверить

- **`docs_search`** — основной. Ключевые слова: `dishka provider`, `dishka scope`, `dishka fastapi setup`, `dishka FromDishka`, `dishka DishkaRoute`, `dishka taskiq integration`, `dishka finalizer`.
- **`fetch_url_content`** — конкретная страница: `https://dishka.readthedocs.io/...`, `https://raw.githubusercontent.com/reagento/dishka/develop/docs/...`.
- **`search_web`** — нестандартный пример, issue, обсуждение.

| Что проверить                                       | Раздел документации          |
| --------------------------------------------------- | ---------------------------- |
| `Provider`, `@provide`, `scope`                     | `docs/provider/`             |
| Скоупы `APP`, `REQUEST`, `SESSION`, `STEP`          | `docs/advanced/scopes/`      |
| Подключение к FastAPI, `setup_dishka`, `FromDishka` | `docs/integrations/fastapi/` |
| Подключение к воркерам (TaskIQ, arq, FastStream)    | `docs/integrations/`         |
| Финализаторы (`yield`-провайдеры, `AsyncIterable`)  | `docs/advanced/`             |
| Композиция провайдеров, `make_async_container`      | `docs/container/`            |

Обязательно сверить: точную сигнатуру `@provide` и `scope`; имя фабрики контейнера (`make_async_container` / `make_container`) и её аргументы; актуальный список скоупов; сигнатуру `setup_dishka` и порядок аргументов; путь импорта `FromDishka[T]`; нужен ли `@inject`; интеграцию под воркер (TaskIQ, arq, Celery, FastStream) и управление `REQUEST`-scope на задачу; объявление финализаторов (`AsyncIterable` / `Iterable`).

### Что делать при расхождении

**Порядок приоритетов:** документация библиотеки → `.kodarules` → скиллы → `KODA.md`.

1. **Верь документации.** Скилл описывает целевую архитектуру; документация — как её реализовать в текущей версии.
2. **Не копируй код из скилла слепо.** Особенно строки с `Provider`, `@provide`, `FromDishka`, `setup_dishka`, `container.get(...)`.
3. **Обнови скилл**, если изменился не API, а паттерн.

### Что остаётся верным независимо от версии Dishka

- **Один контейнер на всё приложение.**
- **Скоупы по времени жизни.** Конфиг и engine — `APP`, всё что работает с транзакцией — `REQUEST`.
- **Привязка порт → реализация — только в провайдерах.**
- **Провайдеры модулей — в `bootstrap/providers/`, общие — в `core/providers.py`.**
- **В entry point — только создание контейнера и получение корневого объекта.**

---

## Чек-лист

**Структура и зависимости**

- [ ] У каждого модуля одинаковый набор папок; один модуль — одна бизнес-область.
- [ ] В модуле нет `dependencies.py` и `provider.py`; `core` не знает про `modules`.
- [ ] `bootstrap` — единственное место сборки контейнера.
- [ ] Провайдеры модулей — в `bootstrap/providers/<module>.py`, общие — в `core/providers.py`.
- [ ] Привязка порт → реализация сделана **только** в провайдерах.
- [ ] `container.py` собирает провайдеры из `core` и `bootstrap/providers/`.

**Dishka**

- [ ] Один контейнер на всё приложение, собирается в `bootstrap/container.py`.
- [ ] HTTP подключает контейнер через `setup_dishka`; воркеры / CLI / планировщики — через `container.get(...)`.
- [ ] В эндпоинтах — `FromDishka[T]`, не `Depends` для бизнес-зависимостей.
- [ ] Роутеры используют `route_class=DishkaRoute`.
- [ ] `@inject` — только для `Depends`-функций, WebSocket и чужих роутеров.
- [ ] `FastapiProvider()` добавлен в контейнер, если в провайдерах используется `Request`.
- [ ] Нет «голых» типов (`str`, `int`, `dict`) среди зависимостей; в тестах и CI — `ValidationSettings`.
- [ ] Scope выбран по времени жизни: `APP` для engine и конфига, `REQUEST` для сессии и UoW.
- [ ] `orm_registry.py` содержит импорты моделей всех модулей.
- [ ] **Перед написанием кода синтаксис проверен через `docs_search` / `fetch_url_content`.**

**Импорты**

- [ ] `domain` не импортирует FastAPI, SQLAlchemy, Pydantic, Dishka.
- [ ] `application` не импортирует `infrastructure`, `presentation` и Dishka.
- [ ] `presentation` не импортирует `infrastructure`.
- [ ] Между модулями — только `public.py`; `core` не импортирует `modules`.

**Домен**

- [ ] Сущности мутабельны, с поведением; VO иммутабельны, с валидацией в `__post_init__`.
- [ ] Сущности — `@dataclass(slots=True, eq=False)` + свои `__eq__`/`__hash__` по `_id`.
- [ ] Поля сущностей — `_name` + `@property`, без публичных сеттеров.
- [ ] Все доменные методы идемпотентны: повторный вызов — `return`, без исключения.
- [ ] Исключения наследуются от базовых в `core.domain`.
- [ ] Нет `HTTPException` и `async` методов в домене.
- [ ] `datetime.now(UTC)`, не наивное время.
- [ ] PK сущности — `UUID`, не `int`.
- [ ] Сообщения доменных исключений — на английском.

**Транзакции**

- [ ] Репозиторий делает `flush`, не `commit`; провайдер сессии не вызывает `commit`.
- [ ] `commit` — только в use case через `UnitOfWork`.
- [ ] Use case — `@dataclass(slots=True)`, зависимости в конструкторе, единственный метод `async execute(...)`.
- [ ] Репозиторий и UoW живут в одном `Scope.REQUEST` и получают одну сессию.
- [ ] Уникальность защищена `UNIQUE`-констрейнтом.
- [ ] `IntegrityError` → `rollback` в репозитории, затем доменное исключение.

**Ошибки**

- [ ] HTTP-статусы — в одном глобальном обработчике HTTP-точки входа.
- [ ] В роутерах нет `try/except`; порядок маппинга — от частных к общим.
- [ ] Не-HTTP точки входа обрабатывают `DomainError` сами.

**Порты и границы**

- [ ] `Protocol`, не `ABC`; живут в `application/ports/`.
- [ ] Принимают и возвращают VO и сущности, не примитивы и не ORM-модели.
- [ ] Общие порты — в `core/ports.py`.
- [ ] Привязка к реализации — только в Dishka-провайдерах.
- [ ] `public.py` содержит только DTO и фасад; сущности и ORM-модели наружу не отдаются.
- [ ] Связь между модулями — по ID.

---

## Что НЕ входит в эти правила

Подключается поверх, когда появляется реальная необходимость: UnitOfWork с контекстным менеджером (`__aenter__`/`__aexit__`), CQRS и read-модели, шина событий, кэш и очереди, `import-linter` в CI, тестовая БД, конкретные библиотеки (bcrypt, JWT).

Правила из этого скилла остаются неизменными независимо от того, что из этого списка подключено.
