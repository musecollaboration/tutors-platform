# ruff: noqa: I001
from app.bootstrap.container import create_container
from app.bootstrap.http.app import create_app
from httpx import ASGITransport
from fastapi import FastAPI
import pytest
import httpx
from collections.abc import AsyncIterator
from tests.validation import VALIDATION_SETTINGS
import os

# Настройки должны быть заданы до импорта приложения: реальные переменные
# окружения имеют приоритет над .env при создании Settings().
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")


@pytest.fixture
def app() -> FastAPI:
    """Default app with the production container."""
    # Прод-граф тоже валидируем: конфликты провайдеров падают при создании
    # контейнера, а не превращаются в ложно-зелёный тест.
    return create_app(container=create_container(VALIDATION_SETTINGS))


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
