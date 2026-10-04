from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.ports import UnitOfWork
from app.modules.auth.application.ports.refresh_token_repository import RefreshTokenRepository
from app.modules.auth.application.ports.token_service import TokenService


@dataclass(slots=True)
class Logout:
    tokens: TokenService
    refresh_tokens: RefreshTokenRepository
    uow: UnitOfWork

    async def execute(self, refresh_token: str) -> None:
        """Revoke a refresh token. Idempotent: unknown/already revoked — no error."""
        token_hash = self.tokens.hash_token(refresh_token)
        stored = await self.refresh_tokens.get_by_hash(token_hash)

        if stored is None or stored.is_revoked:
            # Токен уже неактивен или никогда не был — выходим тихо.
            # Logout должен быть идемпотентным.
            return

        stored.revoke(datetime.now(UTC))
        await self.refresh_tokens.update(stored)
        await self.uow.commit()
