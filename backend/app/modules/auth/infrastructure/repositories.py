from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.auth.domain.exceptions import RefreshTokenNotFoundError
from app.modules.auth.infrastructure.mappers import (
    refresh_token_to_entity,
    refresh_token_to_model,
)
from app.modules.auth.infrastructure.models import RefreshTokenModel


class SqlAlchemyRefreshTokenRepository:
    """SQLAlchemy implementation of RefreshTokenRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        model = await self._session.scalar(select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash))
        return refresh_token_to_entity(model) if model else None

    async def add(self, token: RefreshToken) -> RefreshToken:
        model = refresh_token_to_model(token)
        self._session.add(model)
        await self._session.flush()
        return refresh_token_to_entity(model)

    async def update(self, token: RefreshToken) -> None:
        model = await self._session.get(RefreshTokenModel, token.id)
        if model is None:
            raise RefreshTokenNotFoundError(f"RefreshToken {token.id} not found")
        # Токен иммутабелен по остальным полям: обновляем только revoked_at.
        model.revoked_at = token.revoked_at
        await self._session.flush()
