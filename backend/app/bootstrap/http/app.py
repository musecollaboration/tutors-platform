from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap.container import create_container
from app.bootstrap.http.error_handlers import register_error_handlers
from app.core.config import settings
from app.modules.auth.presentation.router import router as auth_router
from app.modules.users.presentation.router import router as users_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await app.state.dishka_container.close()


def create_app(container: AsyncContainer | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Pass a custom ``container`` to substitute providers (e.g. in tests).
    """
    if container is None:
        container = create_container()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    setup_dishka(container=container, app=app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    register_error_handlers(app)
    app.include_router(users_router, prefix=API_PREFIX)
    app.include_router(auth_router, prefix=API_PREFIX)

    return app
