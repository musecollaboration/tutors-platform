from dataclasses import dataclass

from app.core.ports import UnitOfWork
from app.modules.users.application.dto.registered_user import RegisteredUser
from app.modules.users.application.ports.account_repository import AccountRepository
from app.modules.users.application.ports.password_hasher import PasswordHasher
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.entities.user import User
from app.modules.users.domain.exceptions import EmailAlreadyTakenError
from app.modules.users.domain.value_objects.email import Email
from app.modules.users.domain.value_objects.full_name import FullName
from app.modules.users.domain.value_objects.password import Password


@dataclass(slots=True)
class RegisterUser:
    users: UserRepository
    accounts: AccountRepository
    hasher: PasswordHasher
    uow: UnitOfWork

    async def execute(self, full_name: str, email: str, password: str) -> RegisteredUser:
        full_name_vo = FullName(full_name)
        email_vo = Email(email)
        password_vo = Password(password)

        if await self.accounts.get_by_email(email_vo):
            raise EmailAlreadyTakenError(f"Email {email} is already taken")

        user = User.create(full_name_vo)
        user = await self.users.add(user)

        account = Account.create(
            user_id=user.id,
            email=email_vo,
            password_hash=await self.hasher.hash(password_vo.value),
        )
        await self.accounts.add(account)

        await self.uow.commit()
        return RegisteredUser(
            id=user.id,
            full_name=user.full_name.value,
            email=account.email,
            is_active=user.is_active,
            created_at=user.created_at,
        )
