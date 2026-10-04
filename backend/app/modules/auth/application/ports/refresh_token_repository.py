from typing import Protocol

from app.modules.auth.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(Protocol):
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    async def add(self, token: RefreshToken) -> RefreshToken: ...

    async def update(self, token: RefreshToken) -> None: ...
