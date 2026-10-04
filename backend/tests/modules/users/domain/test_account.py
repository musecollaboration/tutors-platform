from uuid import UUID, uuid4

import pytest

from app.modules.users.domain.entities.account import Account
from app.modules.users.domain.value_objects.email import Email


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def account(user_id: UUID) -> Account:
    return Account.create(
        user_id=user_id,
        email=Email("user@example.com"),
        password_hash="hashed-password",
    )


class TestCreate:
    def test_assigns_generated_id(self, account: Account) -> None:
        assert isinstance(account.id, UUID)

    def test_stores_user_id(self, account: Account, user_id: UUID) -> None:
        assert account.user_id == user_id

    def test_stores_email(self, account: Account) -> None:
        assert account.email == Email("user@example.com")

    def test_stores_password_hash(self, account: Account) -> None:
        assert account.password_hash == "hashed-password"

    def test_created_at_is_timezone_aware(self, account: Account) -> None:
        assert account.created_at.tzinfo is not None

    def test_updated_at_is_none(self, account: Account) -> None:
        assert account.updated_at is None

    def test_not_locked_by_default(self, account: Account) -> None:
        assert account.is_locked is False

    def test_ids_are_unique(self, user_id: UUID) -> None:
        first = Account.create(user_id, Email("a@example.com"), "hash")
        second = Account.create(user_id, Email("b@example.com"), "hash")
        assert first.id != second.id


class TestChangePassword:
    def test_updates_hash(self, account: Account) -> None:
        account.change_password("new-hash")
        assert account.password_hash == "new-hash"

    def test_sets_updated_at(self, account: Account) -> None:
        account.change_password("new-hash")
        assert account.updated_at is not None
        assert account.updated_at.tzinfo is not None


class TestLock:
    def test_locks_account(self, account: Account) -> None:
        account.lock()
        assert account.is_locked is True

    def test_sets_updated_at(self, account: Account) -> None:
        account.lock()
        assert account.updated_at is not None

    def test_is_idempotent(self, account: Account) -> None:
        account.lock()
        first_updated_at = account.updated_at
        account.lock()
        assert account.is_locked is True
        assert account.updated_at is first_updated_at


class TestUnlock:
    def test_unlocks_account(self, account: Account) -> None:
        account.lock()
        account.unlock()
        assert account.is_locked is False

    def test_is_idempotent_when_not_locked(self, account: Account) -> None:
        account.unlock()
        assert account.is_locked is False
        assert account.updated_at is None

    def test_is_idempotent_when_locked(self, account: Account) -> None:
        account.lock()
        account.unlock()
        first_updated_at = account.updated_at
        account.unlock()
        assert account.updated_at is first_updated_at


class TestEquality:
    def test_equal_by_id(self, account: Account) -> None:
        clone = Account(
            _id=account.id,
            _user_id=account.user_id,
            _email=account.email,
            _password_hash=account.password_hash,
            _created_at=account.created_at,
        )
        assert account == clone
        assert hash(account) == hash(clone)

    def test_different_ids_are_not_equal(self, user_id: UUID) -> None:
        first = Account.create(user_id, Email("a@example.com"), "hash")
        second = Account.create(user_id, Email("a@example.com"), "hash")
        assert first != second


class TestStringRepresentation:
    def test_str_contains_id_and_email(self, account: Account) -> None:
        text = str(account)
        assert str(account.id) in text
        assert "user@example.com" in text
