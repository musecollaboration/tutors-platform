from uuid import UUID

from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.entities.user import User
from app.modules.users.domain.exceptions import EmailAlreadyTakenError
from app.modules.users.domain.value_objects.email import Email


class FakeUserRepository:
    """In-memory UserRepository implementation."""

    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def add(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def update(self, user: User) -> None:
        self.users[user.id] = user


class FakeAccountRepository:
    """In-memory AccountRepository implementation with unique-email check."""

    def __init__(self) -> None:
        self.accounts: dict[UUID, Account] = {}

    async def get_by_id(self, account_id: UUID) -> Account | None:
        return self.accounts.get(account_id)

    async def get_by_email(self, email: Email) -> Account | None:
        for account in self.accounts.values():
            if account.email.value == email.value:
                return account
        return None

    async def add(self, account: Account) -> Account:
        if await self.get_by_email(account.email) is not None:
            raise EmailAlreadyTakenError(f"Email {account.email.value} is already taken")
        self.accounts[account.id] = account
        return account

    async def update(self, account: Account) -> None:
        self.accounts[account.id] = account


class FakePasswordHasher:
    """In-memory PasswordHasher implementation. No real cryptography."""

    async def hash(self, password: str) -> str:
        return f"hashed:{password}"

    async def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeUnitOfWork:
    """In-memory UnitOfWork implementation. Records commit/rollback calls."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
