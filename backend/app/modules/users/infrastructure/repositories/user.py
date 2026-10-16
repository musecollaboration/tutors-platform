from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.domain.entities.user import User
from app.modules.users.domain.exceptions import UserNotFoundError
from app.modules.users.infrastructure.mappers import user_to_entity, user_to_model
from app.modules.users.infrastructure.models import UserModel


class SqlAlchemyUserRepository:
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return user_to_entity(model) if model else None

    async def add(self, user: User) -> User:
        model = user_to_model(user)
        self._session.add(model)
        await self._session.flush()
        return user_to_entity(model)

    async def update(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise UserNotFoundError(f"User {user.id} not found")
        model.full_name = user.full_name.value
        model.is_active = user.is_active
        model.updated_at = user.updated_at
        await self._session.flush()
