from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.ports import UnitOfWork
from app.modules.auth.application.dto.token_pair import TokenPair
from app.modules.auth.application.ports.refresh_token_repository import RefreshTokenRepository
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.auth.domain.exceptions import InvalidTokenError


@dataclass(slots=True)
class Refresh:
    tokens: TokenService
    refresh_tokens: RefreshTokenRepository
    uow: UnitOfWork

    async def execute(self, refresh_token: str) -> TokenPair:
        # Decode проверяет подпись, exp и type == "refresh".
        # Если что-то не так — TokenExpiredError / InvalidTokenError.
        self.tokens.decode(refresh_token, expected_type="refresh")

        token_hash = self.tokens.hash_token(refresh_token)
        stored = await self.refresh_tokens.get_by_hash(token_hash)

        now = datetime.now(UTC)
        if stored is None or not stored.is_active(now):
            # Токен не найден, отозван или просрочен.
            # Не раскрываем, что именно — общий InvalidTokenError.
            raise InvalidTokenError("Refresh token is not active")

        # Ротация: старый отзываем, выпускаем новый.
        stored.revoke(now)
        await self.refresh_tokens.update(stored)

        new_access = self.tokens.create_access_token(stored.user_id)
        new_refresh_raw, new_refresh_expires_at = self.tokens.create_refresh_token(stored.user_id)

        new_refresh = RefreshToken.create(
            user_id=stored.user_id,
            token_hash=self.tokens.hash_token(new_refresh_raw),
            expires_at=new_refresh_expires_at,
            created_at=now,
        )
        await self.refresh_tokens.add(new_refresh)

        await self.uow.commit()
        return TokenPair(access_token=new_access, refresh_token=new_refresh_raw)
