from uuid import UUID

import pytest

from app.modules.users.domain.entities.user import User
from app.modules.users.domain.value_objects.full_name import FullName


@pytest.fixture
def user() -> User:
    return User.create(FullName("Иван Иванов"))


class TestCreate:
    def test_assigns_generated_id(self, user: User) -> None:
        assert isinstance(user.id, UUID)

    def test_stores_full_name(self, user: User) -> None:
        assert user.full_name == FullName("Иван Иванов")

    def test_is_active_by_default(self, user: User) -> None:
        assert user.is_active is True

    def test_created_at_is_timezone_aware(self, user: User) -> None:
        assert user.created_at.tzinfo is not None

    def test_updated_at_is_none(self, user: User) -> None:
        assert user.updated_at is None

    def test_ids_are_unique(self) -> None:
        first = User.create(FullName("Иван Иванов"))
        second = User.create(FullName("Пётр Петров"))
        assert first.id != second.id


class TestChangeFullName:
    def test_updates_name(self, user: User) -> None:
        user.change_full_name(FullName("Пётр Петров"))
        assert user.full_name == FullName("Пётр Петров")

    def test_sets_updated_at(self, user: User) -> None:
        user.change_full_name(FullName("Пётр Петров"))
        assert user.updated_at is not None
        assert user.updated_at.tzinfo is not None

    def test_is_idempotent_for_same_name(self, user: User) -> None:
        user.change_full_name(FullName("Иван Иванов"))
        assert user.updated_at is None


class TestActivate:
    def test_is_idempotent_when_already_active(self, user: User) -> None:
        user.activate()
        assert user.is_active is True
        assert user.updated_at is None

    def test_reactivates_deactivated_user(self, user: User) -> None:
        user.deactivate()
        user.activate()
        assert user.is_active is True


class TestDeactivate:
    def test_deactivates_user(self, user: User) -> None:
        user.deactivate()
        assert user.is_active is False

    def test_sets_updated_at(self, user: User) -> None:
        user.deactivate()
        assert user.updated_at is not None

    def test_is_idempotent(self, user: User) -> None:
        user.deactivate()
        first_updated_at = user.updated_at
        user.deactivate()
        assert user.is_active is False
        assert user.updated_at is first_updated_at


class TestEquality:
    def test_equal_by_id(self, user: User) -> None:
        clone = User(
            _id=user.id,
            _full_name=user.full_name,
            _is_active=user.is_active,
            _created_at=user.created_at,
        )
        assert user == clone
        assert hash(user) == hash(clone)

    def test_different_ids_are_not_equal(self) -> None:
        first = User.create(FullName("Иван Иванов"))
        second = User.create(FullName("Иван Иванов"))
        assert first != second


class TestStringRepresentation:
    def test_str_contains_id_and_name(self, user: User) -> None:
        text = str(user)
        assert str(user.id) in text
        assert "Иван Иванов" in text
