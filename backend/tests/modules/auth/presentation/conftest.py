from collections.abc import AsyncIterator

import pytest
from dishka import AsyncContainer, Provider, Scope, ValidationSettings, make_async_container, provide
from fastapi import FastAPI

from app.bootstrap.http.app import create_app
from app.core.ports import UnitOfWork
from app.modules.auth.application.ports.refresh_token_repository import RefreshTokenRepository
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.application.use_cases.refresh import Refresh
from tests.modules.auth.application.fakes import (
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUnitOfWork,
)


class TestAuthProvider(Provider):
    """Auth module provider wired to in-memory fakes."""

    scope = Scope.REQUEST

    token_service = provide(FakeTokenService, provides=TokenService, scope=Scope.APP)
    refresh_token_repository = provide(FakeRefreshTokenRepository, provides=RefreshTokenRepository)
    unit_of_work = provide(FakeUnitOfWork, provides=UnitOfWork)
    refresh = provide(Refresh)


# Строгая валидация графа: конфликты фабрик ловятся при создании контейнера.
_VALIDATION_SETTINGS = ValidationSettings(
    implicit_override=True,
    nothing_overridden=True,
    nothing_decorated=True,
)


@pytest.fixture
async def test_container() -> AsyncIterator[AsyncContainer]:
    container = make_async_container(TestAuthProvider(), validation_settings=_VALIDATION_SETTINGS)
    yield container
    await container.close()


@pytest.fixture
async def app(test_container: AsyncContainer) -> FastAPI:
    """App with the test container substituted for the production one."""
    return create_app(container=test_container)
