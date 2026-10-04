from dishka import AsyncContainer, make_async_container

from app.bootstrap.providers.auth import AuthProvider
from app.bootstrap.providers.users import UsersProvider
from app.core.providers import CoreProvider


def create_container() -> AsyncContainer:
    return make_async_container(
        CoreProvider(),
        UsersProvider(),
        AuthProvider(),
    )
