from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.auth.domain.exceptions import InvalidTokenError
from app.modules.auth.domain.value_objects.token_payload import TokenPayload


class FakeTokenService:
    """In-memory TokenService. Any token is rejected as invalid."""

    def create_access_token(self, user_id: UUID) -> str:
        return f"access:{user_id}"

    def create_refresh_token(self, user_id: UUID) -> tuple[str, datetime]:
        return f"refresh:{user_id}", datetime.now(UTC)

    def decode(self, token: str, expected_type: Literal["access", "refresh"]) -> TokenPayload:
        raise InvalidTokenError("Token is invalid")

    def hash_token(self, token: str) -> str:
        return f"hash:{token}"


class FakeRefreshTokenRepository:
    """In-memory RefreshTokenRepository implementation."""

    def __init__(self) -> None:
        self.tokens: dict[str, RefreshToken] = {}

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.tokens.get(token_hash)

    async def add(self, token: RefreshToken) -> RefreshToken:
        self.tokens[token.token_hash] = token
        return token

    async def update(self, token: RefreshToken) -> None:
        self.tokens[token.token_hash] = token


class FakeUnitOfWork:
    """In-memory UnitOfWork implementation. Records commit/rollback calls."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
