---
name: fastapi-project
description: Правила и конвенции FastAPI для проекта. DI — через Dishka (не через Depends). Используй при работе с FastAPI API, Pydantic-моделями, streaming-ответами (SSE), раздачей frontend. Держит код на FastAPI чистым и актуальным.
---

# FastAPI

Проектный форк официального скилла FastAPI. Адаптирован под стек проекта: DI через Dishka, без `Depends` для бизнес-зависимостей.

> **Не открывай ссылку ниже.** Это источник для ручного обновления скилла разработчиком. Содержимое по ссылке может противоречить правилам проекта (использует `Depends`, не знает про Dishka). Работай только с этим файлом.
>
> Источник для ручной синхронизации: https://github.com/fastapi/fastapi/blob/master/fastapi/.agents/skills/fastapi/SKILL.md

## Быстрая навигация

- **Раздача frontend**: `app.frontend()` или `router.frontend()` для собранных статичных файлов; см. [Раздача frontend](#раздача-frontend).
- **Server-Sent Events (SSE)**: `response_class=EventSourceResponse` и `yield`; см. [Streaming](#streaming-json-lines-sse-bytes).
- **JSON Lines и потоковая передача байтов**: см. раздел Streaming ниже.
- **DI**: в проекте — **Dishka**, не `Depends`. См. [Интеграция Dishka](#интеграция-dishka).
- **Модели ответа**: предпочитай аннотацию возврата; `response_model` — когда публичная схема отличается от внутреннего возврата.
- **Pydantic-модели**: не использовать `...` и `RootModel`.
- **Роутинг**: `prefix` и `tags` объявлять на `APIRouter`. DI — через `route_class=DishkaRoute`.
- **Инструменты**: poetry, Ruff, ty, Asyncer, HTTPX — см. разделы [Tooling](#tooling) и [Другие библиотеки](#другие-библиотеки).

## CLI `fastapi`

Запуск dev-сервера с автоперезагрузкой:

```bash
fastapi dev
```

Запуск production-сервера:

```bash
fastapi run
```

Предпочтительно указывать entrypoint в `pyproject.toml`:

```toml
[tool.fastapi]
entrypoint = "my_app.main:app"
```

Если указать entrypoint нельзя, передавай путь к файлу приложения:

```bash
fastapi dev my_app/main.py
```

## Использование `Annotated`

Всегда предпочитай `Annotated` для объявления параметров. Это сохраняет сигнатуру функции рабочей в других контекстах, уважает типы и позволяет переиспользовать объявления.

Используй `Annotated` для параметров, включая `Path`, `Query`, `Header`:

```python
from typing import Annotated

from fastapi import FastAPI, Path, Query

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(ge=1, description="The item ID")],
    q: Annotated[str | None, Query(max_length=50)] = None,
):
    return {"message": "Hello World"}
```

## Не использовать `...` для path operations и Pydantic-моделей

Не используй `...` как значение по умолчанию для обязательных параметров или полей модели. Это не нужно и не рекомендуется.

```python
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0)


@app.post("/items/")
async def create_item(item: Item, project_id: Annotated[int, Query()]):
    return item
```

## Тип возврата или response_model

Когда возможно — указывай тип возврата. Он используется для валидации, фильтрации, документирования и сериализации ответа.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    description: str | None = None


@app.get("/items/me")
async def get_item() -> Item:
    return Item(name="Plumbus", description="All-purpose home device")
```

Типы возврата и response_model фильтруют данные, чтобы не выставлять наружу лишнее, и позволяют Pydantic сериализовать данные на стороне Rust для производительности.

Используй `response_model`, когда тип возвращаемого значения не совпадает с публичной схемой, которую нужно валидировать, фильтровать, документировать и сериализовать.

## Производительность

Не используй `ORJSONResponse` или `UJSONResponse` — они устарели.

Вместо этого объяви тип возврата или `response_model`. Pydantic сам сериализует данные на стороне Rust.

## Подключение роутеров

При объявлении роутеров добавляй параметры уровня роутера (`prefix`, `tags`) на сам `APIRouter`, а не в `include_router()`.

```python
from fastapi import APIRouter, FastAPI

app = FastAPI()


router = APIRouter(
    prefix="/items",
    tags=["items"],
)


@router.get("/")
async def list_items():
    return []


app.include_router(router)
```

Для DI в роутере — `route_class=DishkaRoute`, см. [Интеграция Dishka](#интеграция-dishka).

## Раздача frontend

Используй `app.frontend()` для раздачи собранного статичного frontend-приложения (директория, сгенерированная Vite, Astro, Angular, Svelte, Vue или похожим инструментом).

```python
from fastapi import FastAPI

app = FastAPI()

app.frontend("/", directory="dist")
```

Используй `router.frontend()`, когда frontend относится к `APIRouter`. Префикс роутера работает как обычно.

```python
from fastapi import APIRouter, FastAPI

app = FastAPI()
router = APIRouter(prefix="/admin")

router.frontend("/", directory="admin-dist")
app.include_router(router)
```

`app.frontend()` и `router.frontend()` — маршруты с низким приоритетом: сначала матчатся обычные API-роуты, затем файлы frontend и client-side routing fallback. Используй для single-page-приложений и собранных frontend-файлов вместо ручного монтирования `StaticFiles`.

## Интеграция Dishka

Dishka предоставляет интеграцию через `dishka.integrations.fastapi`. Основные компоненты:

| Компонент                      | Зачем                                                               |
| ------------------------------ | ------------------------------------------------------------------- |
| `setup_dishka(container, app)` | Связывает контейнер с FastAPI, управляет `Scope.REQUEST`            |
| `FromDishka[T]`                | Маркер в сигнатуре: «этот параметр — из контейнера»                 |
| `DishkaRoute`                  | `route_class` для роутера: автоинъекция во всех эндпоинтах          |
| `@inject`                      | Альтернатива `DishkaRoute`; нужен для `Depends`-функций и WebSocket |
| `FastapiProvider()`            | Провайдер для доступа к `Request` и `WebSocket` внутри провайдеров  |

### `setup_dishka(container, app)`

Связывает контейнер с FastAPI. Добавляет middleware, который:

- открывает `Scope.REQUEST` на каждый запрос;
- закрывает scope после ответа, вызывая финализацию ресурсов;
- передаёт контекст запроса (`Request`, `WebSocket`) в провайдеры при необходимости.

```python
from dishka.integrations.fastapi import setup_dishka

container = create_container()
app = FastAPI(lifespan=lifespan)
setup_dishka(container, app)
```

### `FromDishka[T]` — маркер в сигнатуре

Говорит FastAPI: «этот параметр не из path/query/body — его предоставит Dishka». Синоним `Annotated[T, FromComponent()]`. Полная форма нужна только при работе с несколькими компонентами: `Annotated[T, FromComponent("X")]`.

### `DishkaRoute` — автоинъекция для роутера

`route_class=DishkaRoute` включает обработку `FromDishka[T]` для всех эндпоинтов роутера. **В проекте используется именно он.**

```python
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

router = APIRouter(
    prefix="/users",
    tags=["users"],
    route_class=DishkaRoute,
)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterUserRequest,
    use_case: FromDishka[RegisterUser],
) -> UserResponse:
    user = await use_case.execute(body.email, body.password)
    return UserResponse.from_entity(user)
```

**Как работает:** `DishkaRoute` — наследник `APIRoute` из FastAPI. При создании роутера FastAPI использует его вместо стандартного. Он резолвит `FromDishka[T]` до вызова хендлера. Роутер остаётся чистым — без `@inject` и без `Depends(get_use_case)`.

**Почему выбран он, а не `@inject`:**

1. **Ставится один раз на роутер.** Новые эндпоинты автоматически получают инъекцию.
2. **Нельзя забыть.** С `@inject` легко пропустить декоратор над новым хендлером — и `FromDishka[T]` молча не сработает.
3. **Меньше шума в коде.** Не надо помнить про `@inject` над каждой функцией.

**Ограничение:** `DishkaRoute` работает только с HTTP. Для WebSocket — `@inject` (см. ниже).

### `@inject` — когда всё-таки нужен

`@inject` не устарел и не запрещён. Остаётся в трёх случаях.

**Случай 1. `Depends`-функции.**

Если используется FastAPI-native `Depends` (например, `OAuth2PasswordBearer` для авторизации), то внутри такой функции `FromDishka[T]` работает **только с `@inject`**. `route_class=DishkaRoute` на роутере `Depends`-функции не обрабатывает.

```python
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer

from app.modules.auth.application.use_cases import GetCurrentUser
from app.modules.auth.domain.entities import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@inject                                            # ← обязательно
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    use_case: FromDishka[GetCurrentUser],          # ← работает только с @inject
) -> User:
    return use_case.execute(token)


router = APIRouter(route_class=DishkaRoute)


@router.get("/me")
async def read_me(
    user: Annotated[User, Depends(get_current_user)],
):
    return user
```

Правило из документации Dishka:

> `@inject` требуется для `Depends`-функций, даже если используется `DishkaRoute`.

**Случай 2. WebSocket-эндпоинты.**

`DishkaRoute` работает только с HTTP. Для WebSocket — `@inject`.

WebSocket использует **другой набор скоупов**:

```
APP → SESSION → REQUEST
```

- `APP` — время жизни приложения.
- `SESSION` — время жизни одного WebSocket-соединения.
- `REQUEST` — одно сообщение в соединении.

`@inject` в WebSocket даёт доступ только к `SESSION`-объектам. Для `REQUEST` — вход в scope вручную:

```python
from dishka import AsyncContainer
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import WebSocket


@inject
async def websocket_endpoint(
    websocket: WebSocket,
    session_service: FromDishka[SessionService],       # Scope.SESSION
    container: FromDishka[AsyncContainer],             # Scope.SESSION
) -> None:
    await websocket.accept()

    while True:
        data = await websocket.receive_text()

        async with container() as request_container:
            message_service = await request_container.get(MessageService)
            await message_service.handle(data)
```

**Случай 3. Роутер создаётся не тобой.**

Например, сторонняя библиотека отдаёт готовый `APIRouter`. Поставить `route_class=DishkaRoute` на него нельзя — придётся вешать `@inject` на хендлеры.

### `FastapiProvider()` — доступ к `Request` и `WebSocket`

Если в провайдере нужен объект `Request` (например, для извлечения заголовка `Authorization` или `X-Request-ID`), в контейнер надо добавить `FastapiProvider()`.

```python
# core/providers.py
from dishka import Provider, Scope, provide
from fastapi import Request


class RequestContextProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_request_id(self, request: Request) -> str:
        return request.headers.get("X-Request-ID", "")
```

```python
# bootstrap/container.py
from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider


def create_container():
    return make_async_container(
        CoreProvider(),
        UsersProvider(),
        FastapiProvider(),   # ← обязательно, если используем Request
    )
```

Без `FastapiProvider()` Dishka не знает, откуда взять `Request`, и упадёт при сборке контейнера.

**Когда понадобится:** когда появится auth-middleware и `CurrentUser` из JWT.

### `lifespan` и закрытие контейнера

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


app = FastAPI(lifespan=lifespan)
```

Без `close()` APP-scope не финализируется: engine, пул соединений, HTTP-клиенты не закроются.

### Порядок подключения

```python
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app.bootstrap.providers.users import UsersProvider
from app.core.providers import CoreProvider
from app.modules.users.presentation.router import router as users_router


def create_app() -> FastAPI:
    # 1. Собрать контейнер
    container = make_async_container(
        CoreProvider(),
        UsersProvider(),
    )

    # 2. Создать app и подключить контейнер
    app = FastAPI(lifespan=lifespan)
    setup_dishka(container, app)

    # 3. Подключить роутеры
    app.include_router(users_router, prefix="/api/v1")

    return app
```

**Порядок важен:** `make_async_container` → `setup_dishka` → `include_router`. Если перепутать — `FromDishka[T]` не будет работать.

### Алиасы для зависимостей

Чтобы не писать `FromDishka[LongName]` в каждом эндпоинте:

```python
# presentation/dependencies.py
from dishka.integrations.fastapi import FromDishka

RegisterUserDep = FromDishka[RegisterUser]
```

В роутере:

```python
async def register_user(
    body: RegisterUserRequest,
    use_case: RegisterUserDep,
):
    ...
```

### `Depends` — только для FastAPI-native вещей

`Depends` остаётся **только** для встроенных механизмов FastAPI:

- `OAuth2PasswordBearer`
- `HTTPBearer`
- `APIKeyHeader`

Для бизнес-зависимостей (use cases, репозитории, адаптеры, сессии, UoW) — только `FromDishka[T]`.

## Async vs Sync path operations

Используй `async` path operations, только если полностью уверен, что код внутри совместим с async/await и не блокирует.

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/async-items/")
async def read_async_items():
    data = await some_async_library.fetch_items()
    return data


@app.get("/items/")
def read_items():
    data = some_blocking_library.fetch_items()
    return data
```

При сомнении или по умолчанию — используй обычные `def`-функции. Они выполняются в threadpool и не блокируют event loop. Те же правила применяются к провайдерам Dishka: провайдер с `async def` используется в async-контейнере, синхронный провайдер — в sync.

Убедись, что блокирующий код не выполняется внутри `async`-функций. Логика сработает, но это сильно ударит по производительности.

Если нужно смешать блокирующий и async-код — см. Asyncer в разделе [Другие библиотеки](#другие-библиотеки).

## Streaming (JSON Lines, SSE, bytes)

Для стриминга Server-Sent Events используй `response_class=EventSourceResponse` и `yield` элементы из эндпоинта.

```python
from collections.abc import AsyncIterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent

app = FastAPI()


@app.get("/events", response_class=EventSourceResponse)
async def stream_events() -> AsyncIterable[ServerSentEvent]:
    yield ServerSentEvent(data={"status": "started"}, event="status", id="1")
```

Обычные объекты автоматически JSON-сериализуются в поля `data:`. Используй `ServerSentEvent` для полного контроля над полями SSE (`event`, `id`, `retry`, `comment`) и `raw_data` для предварительно отформатированных строк.

Паттерны JSON Lines, Server-Sent Events (`EventSourceResponse`, `ServerSentEvent`) и потоковой передачи байтов (`StreamingResponse`) — см. примеры выше.

## Tooling

poetry — управление пакетами; Ruff — линтинг и форматирование; ty — проверка типов.

## Другие библиотеки

- **Asyncer** — для работы с async/await, конкурентностью, смешивания async и блокирующего кода. Предпочтительнее AnyIO и asyncio.
- **HTTPX** — для HTTP-запросов к внешним API. Предпочтительнее Requests.

## Не использовать Pydantic RootModels

Не используй Pydantic `RootModel`; вместо этого — обычные аннотации типов с `Annotated` и валидацией Pydantic.

```python
from typing import Annotated

from fastapi import Body, FastAPI
from pydantic import Field

app = FastAPI()


@app.post("/items/")
async def create_items(items: Annotated[list[int], Field(min_length=1), Body()]):
    return items
```

FastAPI поддерживает такие аннотации и создаёт Pydantic `TypeAdapter` для них. Типы работают без кастомных wrapper-моделей.

## Одна HTTP-операция — одна функция

Не смешивай HTTP-операции в одной функции. Одна функция на одну HTTP-операцию помогает разделить ответственность и организовать код.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str


@app.get("/items/")
async def list_items():
    return []


@app.post("/items/")
async def create_item(item: Item):
    return item
```
