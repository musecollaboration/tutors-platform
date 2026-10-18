from dishka import AsyncContainer, ValidationSettings, make_async_container

from app.bootstrap.providers.auth import AuthProvider
from app.bootstrap.providers.users import UsersProvider
from app.core.providers import CoreProvider


def create_container(validation_settings: ValidationSettings | None = None) -> AsyncContainer:
    """Create the application container.

    Pass ``validation_settings`` to fail fast on a broken graph
    (used by tests, see tests/validation.py).
    """
    providers = (CoreProvider(), UsersProvider(), AuthProvider())
    if validation_settings is None:
        return make_async_container(*providers)
    return make_async_container(*providers, validation_settings=validation_settings)
