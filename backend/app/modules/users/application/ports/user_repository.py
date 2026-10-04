from typing import Protocol
from uuid import UUID

from app.modules.users.domain.entities.user import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def add(self, user: User) -> User: ...

    async def update(self, user: User) -> None: ...
