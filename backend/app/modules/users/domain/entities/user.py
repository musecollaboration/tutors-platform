from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self
from uuid import UUID, uuid4

from app.modules.users.domain.value_objects.full_name import FullName


@dataclass(slots=True, eq=False)
class User:
    """A person registered in the system."""

    _id: UUID
    _full_name: FullName
    _is_active: bool
    _created_at: datetime
    _updated_at: datetime | None = None

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, User):
            return NotImplemented
        return self._id == value._id

    def __hash__(self) -> int:
        return hash(self._id)

    @classmethod
    def create(cls, full_name: FullName) -> Self:
        return cls(
            _id=uuid4(),
            _full_name=full_name,
            _is_active=True,
            _created_at=datetime.now(UTC),
            _updated_at=None,
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def full_name(self) -> FullName:
        return self._full_name

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    def change_full_name(self, new_name: FullName) -> None:
        if new_name == self._full_name:
            return
        self._full_name = new_name
        self._updated_at = datetime.now(UTC)

    def activate(self) -> None:
        if self._is_active:
            return
        self._is_active = True
        self._updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        if not self._is_active:
            return
        self._is_active = False
        self._updated_at = datetime.now(UTC)

    def __str__(self) -> str:
        return f"User(id={self._id}, full_name={self._full_name.value})"
