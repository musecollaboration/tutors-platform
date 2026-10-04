from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.entities.user import User
from app.modules.users.domain.value_objects.email import Email
from app.modules.users.domain.value_objects.full_name import FullName
from app.modules.users.infrastructure.models import AccountModel, UserModel


def user_to_entity(model: UserModel) -> User:
    """Convert UserModel to User entity."""
    return User(
        _id=model.id,
        _full_name=FullName(model.full_name),
        _is_active=model.is_active,
        _created_at=model.created_at,
        _updated_at=model.updated_at,
    )


def user_to_model(entity: User) -> UserModel:
    """Convert User entity to UserModel."""
    return UserModel(
        id=entity.id,
        full_name=entity.full_name.value,
        is_active=entity.is_active,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def account_to_entity(model: AccountModel) -> Account:
    """Convert AccountModel to Account entity."""
    return Account(
        _id=model.id,
        _user_id=model.user_id,
        _email=Email(model.email),
        _password_hash=model.password_hash,
        _created_at=model.created_at,
        _updated_at=model.updated_at,
        _is_locked=model.is_locked,
    )


def account_to_model(entity: Account) -> AccountModel:
    """Convert Account entity to AccountModel."""
    return AccountModel(
        id=entity.id,
        user_id=entity.user_id,
        email=entity.email.value,
        password_hash=entity.password_hash,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        is_locked=entity.is_locked,
    )
