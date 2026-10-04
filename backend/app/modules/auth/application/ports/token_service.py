from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from app.modules.auth.domain.value_objects.token_payload import TokenPayload


class TokenService(Protocol):
    """JWT operations: create, decode, hash."""

    def create_access_token(self, user_id: UUID) -> str: ...

    def create_refresh_token(self, user_id: UUID) -> tuple[str, datetime]:
        """Return (token, expires_at)."""
        ...

    def decode(
        self,
        token: str,
        expected_type: Literal["access", "refresh"],
    ) -> TokenPayload:
        """Decode and verify. Raise InvalidTokenError / TokenExpiredError."""
        ...

    def hash_token(self, token: str) -> str:
        """Return sha256 hex of the raw token."""
        ...
