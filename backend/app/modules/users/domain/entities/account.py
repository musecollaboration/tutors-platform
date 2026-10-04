from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

from app.modules.users.domain.value_objects.email import Email


@dataclass(slots=True, eq=False)
class Account:
    """Authentication credentials linked to a user. Tracks lock status."""

    _id: UUID
    _user_id: UUID
    _email: Email
    _password_hash: str
    _created_at: datetime
    _updated_at: datetime | None = None
    _is_locked: bool = False

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Account):
            return NotImplemented
        return self._id == value._id

    def __hash__(self) -> int:
        return hash(self._id)

    @classmethod
    def create(cls, user_id: UUID, email: Email, password_hash: str) -> Self:
        return cls(
            _id=uuid4(),
            _user_id=user_id,
            _email=email,
            _password_hash=password_hash,
            _created_at=datetime.now(UTC),
            _is_locked=False,
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def email(self) -> Email:
        return self._email

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def is_locked(self) -> bool:
        return self._is_locked

    def change_password(self, password_hash: str) -> None:
        self._password_hash = password_hash
        self._updated_at = datetime.now(UTC)

    def lock(self) -> None:
        if self._is_locked:
            return
        self._is_locked = True
        self._updated_at = datetime.now(UTC)

    def unlock(self) -> None:
        if not self._is_locked:
            return
        self._is_locked = False
        self._updated_at = datetime.now(UTC)

    def __str__(self) -> str:
        return f"Account(id={self._id}, user_id={self._user_id}, email={self._email})"
