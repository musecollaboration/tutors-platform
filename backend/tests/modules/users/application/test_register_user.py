from uuid import UUID

import pytest

from app.modules.users.application.use_cases.register_user import RegisterUser
from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.exceptions import (
    EmailAlreadyTakenError,
    InvalidEmailError,
    InvalidPasswordError,
)
from app.modules.users.domain.value_objects.email import Email
from tests.modules.users.application.fakes import (
    FakeAccountRepository,
    FakePasswordHasher,
    FakeUnitOfWork,
    FakeUserRepository,
)


@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def account_repo() -> FakeAccountRepository:
    return FakeAccountRepository()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def use_case(
    user_repo: FakeUserRepository,
    account_repo: FakeAccountRepository,
    hasher: FakePasswordHasher,
    uow: FakeUnitOfWork,
) -> RegisterUser:
    return RegisterUser(users=user_repo, accounts=account_repo, hasher=hasher, uow=uow)


async def test_register_success(
    use_case: RegisterUser,
    user_repo: FakeUserRepository,
    account_repo: FakeAccountRepository,
    uow: FakeUnitOfWork,
) -> None:
    result = await use_case.execute("Иван Иванов", "ivan@example.com", "secret123")

    assert isinstance(result.id, UUID)
    assert len(user_repo.users) == 1

    account = await account_repo.get_by_email(Email("ivan@example.com"))
    assert account is not None
    assert account.user_id == result.id
    assert uow.committed is True


async def test_register_email_lowercased(
    use_case: RegisterUser,
    account_repo: FakeAccountRepository,
) -> None:
    await use_case.execute("Иван", "Test@Example.COM", "secret123")

    account = await account_repo.get_by_email(Email("test@example.com"))
    assert account is not None
    assert account.email.value == "test@example.com"


async def test_register_full_name_trimmed(use_case: RegisterUser) -> None:
    result = await use_case.execute("  Иван  ", "ivan@example.com", "secret123")

    assert result.full_name == "Иван"


async def test_register_password_hashed(
    use_case: RegisterUser,
    account_repo: FakeAccountRepository,
) -> None:
    await use_case.execute("Иван", "ivan@example.com", "secret123")

    account = await account_repo.get_by_email(Email("ivan@example.com"))
    assert account is not None
    assert account.password_hash == "hashed:secret123"
    assert account.password_hash != "secret123"


async def test_register_duplicate_email_raises(use_case: RegisterUser) -> None:
    await use_case.execute("Иван", "ivan@example.com", "secret123")

    with pytest.raises(EmailAlreadyTakenError):
        await use_case.execute("Пётр", "ivan@example.com", "secret123")


async def test_register_invalid_email_raises(use_case: RegisterUser) -> None:
    with pytest.raises(InvalidEmailError):
        await use_case.execute("Иван", "not-an-email", "secret123")


async def test_register_short_password_raises(use_case: RegisterUser) -> None:
    with pytest.raises(InvalidPasswordError):
        await use_case.execute("Иван", "ivan@example.com", "short1")


async def test_register_no_commit_on_error(
    use_case: RegisterUser,
    uow: FakeUnitOfWork,
) -> None:
    with pytest.raises(InvalidEmailError):
        await use_case.execute("Иван", "not-an-email", "secret123")

    assert uow.committed is False


class _RecordingAccountRepository(FakeAccountRepository):
    """Fails on add() to prove the user was persisted before the account."""

    def __init__(self, user_repo: FakeUserRepository) -> None:
        super().__init__()
        self._user_repo = user_repo
        self.user_existed_at_add: bool | None = None

    async def add(self, account: Account) -> Account:
        self.user_existed_at_add = account.user_id in self._user_repo.users
        raise RuntimeError("stop before the account is stored")


async def test_register_creates_user_before_account(
    user_repo: FakeUserRepository,
    hasher: FakePasswordHasher,
    uow: FakeUnitOfWork,
) -> None:
    account_repo = _RecordingAccountRepository(user_repo)
    use_case = RegisterUser(
        users=user_repo,
        accounts=account_repo,
        hasher=hasher,
        uow=uow,
    )

    with pytest.raises(RuntimeError):
        await use_case.execute("Иван", "ivan@example.com", "secret123")

    assert account_repo.user_existed_at_add is True
    assert len(user_repo.users) == 1
