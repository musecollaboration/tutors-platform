import asyncio
from uuid import UUID

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.modules.users.application.ports.account_repository import AccountRepository
from app.modules.users.application.ports.password_hasher import PasswordHasher
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.domain.exceptions import InvalidEmailError
from app.modules.users.domain.value_objects.email import Email
from app.modules.users.public import UserSummary

# Dummy hash для timing-защиты. Используется, когда пользователя нет
# или аккаунт заблокирован — чтобы время ответа было одинаковым.
# Значение сгенерировано один раз, в БД не попадает.
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$+VWWItlRFNJpOb9Fksakwg$sNC6ffvqxFQ4uLjmc27Q5OSzV7G1GSvxr8AjVhn7BNQ"


class Argon2PasswordHasher:
    """Password hasher using pwdlib with argon2.

    Argon2 is CPU-bound and blocks the event loop. Therefore hash and verify
    are executed in a thread pool via asyncio.to_thread.
    """

    def __init__(self) -> None:
        self._hash = PasswordHash.recommended()

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hash.hash, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        try:
            return await asyncio.to_thread(self._hash.verify, password, password_hash)
        except UnknownHashError:
            return False


class SqlAlchemyUsersFacade:
    """Implementation of the public UsersFacade backed by repositories.

    Only UserSummary crosses the module boundary: domain entities and value
    objects stay internal. Invalid credentials and malformed emails are reported
    as None, so foreign modules never see this module's domain errors.
    """

    def __init__(
        self,
        users: UserRepository,
        accounts: AccountRepository,
        hasher: PasswordHasher,
    ) -> None:
        self._users = users
        self._accounts = accounts
        self._hasher = hasher

    async def authenticate(self, email: str, password: str) -> UserSummary | None:
        try:
            email_vo = Email(email)
        except InvalidEmailError:
            # Невалидный email — но verify всё равно вызываем,
            # чтобы время ответа не отличалось от «email не найден».
            await self._hasher.verify(password, DUMMY_HASH)
            return None

        account = await self._accounts.get_by_email(email_vo)
        if account is None:
            # Пользователь не найден — тратим столько же времени,
            # сколько на реальную проверку пароля (защита от timing-атак).
            await self._hasher.verify(password, DUMMY_HASH)
            return None

        if account.is_locked:
            # Аккаунт заблокирован — пароль проверяем, но всё равно отказываем.
            await self._hasher.verify(password, account.password_hash)
            return None

        if not await self._hasher.verify(password, account.password_hash):
            return None

        user = await self._users.get_by_id(account.user_id)
        if user is None:
            return None

        return UserSummary(
            id=user.id,
            full_name=user.full_name.value,
            email=account.email.value,
            is_active=user.is_active,
        )

    async def get_summary(self, user_id: UUID) -> UserSummary | None:
        user = await self._users.get_by_id(user_id)
        if user is None:
            return None

        account = await self._accounts.get_by_user_id(user_id)
        if account is None:
            return None

        return UserSummary(
            id=user.id,
            full_name=user.full_name.value,
            email=account.email.value,
            is_active=user.is_active,
        )
