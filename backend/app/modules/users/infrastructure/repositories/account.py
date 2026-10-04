from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.exceptions import EmailAlreadyTakenError
from app.modules.users.domain.value_objects.email import Email
from app.modules.users.infrastructure.mappers import account_to_entity, account_to_model
from app.modules.users.infrastructure.models import AccountModel


class SqlAlchemyAccountRepository:
    """SQLAlchemy implementation of AccountRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, account_id: UUID) -> Account | None:
        model = await self._session.get(AccountModel, account_id)
        return account_to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> Account | None:
        model = await self._session.scalar(select(AccountModel).where(AccountModel.email == email.value))
        return account_to_entity(model) if model else None

    async def get_by_user_id(self, user_id: UUID) -> Account | None:
        model = await self._session.scalar(select(AccountModel).where(AccountModel.user_id == user_id))
        return account_to_entity(model) if model else None

    async def add(self, account: Account) -> Account:
        model = account_to_model(account)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyTakenError(f"Email {account.email.value} is already taken") from exc
        return account_to_entity(model)

    async def update(self, account: Account) -> None:
        model = await self._session.get(AccountModel, account.id)
        if model is None:
            raise LookupError(f"AccountModel {account.id} not found")
        model.email = account.email.value
        model.password_hash = account.password_hash
        model.is_locked = account.is_locked
        model.updated_at = account.updated_at
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyTakenError(f"Email {account.email.value} is already taken") from exc
