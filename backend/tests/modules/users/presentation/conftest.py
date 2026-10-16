from collections.abc import AsyncIterator

import pytest
from dishka import AsyncContainer, Provider, Scope, ValidationSettings, make_async_container, provide
from fastapi import FastAPI

from app.bootstrap.http.app import create_app
from app.core.ports import UnitOfWork
from app.modules.users.application.ports.account_repository import AccountRepository
from app.modules.users.application.ports.password_hasher import PasswordHasher
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.application.use_cases.register_user import RegisterUser
from tests.modules.users.application.fakes import (
    FakeAccountRepository,
    FakePasswordHasher,
    FakeUnitOfWork,
    FakeUserRepository,
)


class TestUsersProvider(Provider):
    """Users module provider wired to in-memory fakes.

    Repositories are APP-scoped so their in-memory state survives across
    HTTP requests within a test (each request opens a new REQUEST scope).
    """

    scope = Scope.REQUEST

    user_repository = provide(FakeUserRepository, provides=UserRepository, scope=Scope.APP)
    account_repository = provide(FakeAccountRepository, provides=AccountRepository, scope=Scope.APP)
    password_hasher = provide(FakePasswordHasher, provides=PasswordHasher)
    unit_of_work = provide(FakeUnitOfWork, provides=UnitOfWork)
    register_user = provide(RegisterUser)


# Строгая валидация графа: конфликты фабрик ловятся при создании контейнера.
_VALIDATION_SETTINGS = ValidationSettings(
    implicit_override=True,
    nothing_overridden=True,
    nothing_decorated=True,
)


@pytest.fixture
async def test_container() -> AsyncIterator[AsyncContainer]:
    container = make_async_container(TestUsersProvider(), validation_settings=_VALIDATION_SETTINGS)
    yield container
    await container.close()


@pytest.fixture
async def app(test_container: AsyncContainer) -> FastAPI:
    """App with the test container substituted for the production one."""
    return create_app(container=test_container)
