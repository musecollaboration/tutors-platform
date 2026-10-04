from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4


@dataclass(slots=True, eq=False)
class RefreshToken:
    """Refresh token entity. Tracks lifecycle (active/revoked/expired)."""

    _id: UUID
    _user_id: UUID
    _token_hash: str
    _expires_at: datetime
    _created_at: datetime
    _revoked_at: datetime | None = None

    @classmethod
    def create(
        cls,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        created_at: datetime,
    ) -> Self:
        return cls(
            _id=uuid4(),
            _user_id=user_id,
            _token_hash=token_hash,
            _expires_at=expires_at,
            _created_at=created_at,
            _revoked_at=None,
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def token_hash(self) -> str:
        return self._token_hash

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def revoked_at(self) -> datetime | None:
        return self._revoked_at

    @property
    def is_revoked(self) -> bool:
        return self._revoked_at is not None

    def is_expired(self, now: datetime) -> bool:
        return self._expires_at <= now

    def is_active(self, now: datetime) -> bool:
        return not self.is_revoked and not self.is_expired(now)

    def revoke(self, now: datetime) -> None:
        """Mark the token as revoked. Idempotent — repeated calls do nothing."""
        if self._revoked_at is not None:
            return
        self._revoked_at = now

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RefreshToken):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
