from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.ports import UnitOfWork
from app.modules.auth.application.dto.token_pair import TokenPair
from app.modules.auth.application.ports.refresh_token_repository import RefreshTokenRepository
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.auth.domain.exceptions import InvalidCredentialsError
from app.modules.users.public import UsersFacade


@dataclass(slots=True)
class Login:
    users: UsersFacade
    tokens: TokenService
    refresh_tokens: RefreshTokenRepository
    uow: UnitOfWork

    async def execute(self, email: str, password: str) -> TokenPair:
        user = await self.users.authenticate(email, password)
        if user is None:
            raise InvalidCredentialsError("Invalid email or password")

        access = self.tokens.create_access_token(user.id)
        refresh_raw, refresh_expires_at = self.tokens.create_refresh_token(user.id)

        refresh_entity = RefreshToken.create(
            user_id=user.id,
            token_hash=self.tokens.hash_token(refresh_raw),
            expires_at=refresh_expires_at,
            created_at=datetime.now(UTC),
        )
        await self.refresh_tokens.add(refresh_entity)

        await self.uow.commit()
        return TokenPair(access_token=access, refresh_token=refresh_raw)
