from typing import Protocol
from uuid import UUID

from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.value_objects.email import Email


class AccountRepository(Protocol):
    async def get_by_id(self, account_id: UUID) -> Account | None: ...

    async def get_by_email(self, email: Email) -> Account | None: ...

    async def get_by_user_id(self, user_id: UUID) -> Account | None: ...

    async def add(self, account: Account) -> Account: ...

    async def update(self, account: Account) -> None: ...
