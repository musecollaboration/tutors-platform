from dishka import Provider, Scope, provide

from app.modules.users.application.ports.account_repository import AccountRepository
from app.modules.users.application.ports.password_hasher import PasswordHasher
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.application.use_cases.register_user import RegisterUser
from app.modules.users.infrastructure.adapters import Argon2PasswordHasher, SqlAlchemyUsersFacade
from app.modules.users.infrastructure.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyUserRepository,
)
from app.modules.users.public import UsersFacade


class UsersProvider(Provider):
    scope = Scope.REQUEST

    user_repository = provide(SqlAlchemyUserRepository, provides=UserRepository)
    account_repository = provide(SqlAlchemyAccountRepository, provides=AccountRepository)
    password_hasher = provide(Argon2PasswordHasher, provides=PasswordHasher)
    users_facade = provide(SqlAlchemyUsersFacade, provides=UsersFacade)
    register_user = provide(RegisterUser)
