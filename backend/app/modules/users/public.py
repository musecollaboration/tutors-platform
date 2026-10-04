from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserSummary:
    """Public snapshot of a user exposed to other modules."""

    id: UUID
    full_name: str
    email: str
    is_active: bool


class UsersFacade(Protocol):
    """Public interface of the users module."""

    async def authenticate(self, email: str, password: str) -> UserSummary | None:
        """Return the user summary when credentials are valid, otherwise None."""
        ...

    async def get_summary(self, user_id: UUID) -> UserSummary | None:
        """Return the user summary by id, or None when the user does not exist."""
        ...
