from dataclasses import FrozenInstanceError

import pytest

from app.modules.users.domain.exceptions import InvalidPasswordError
from app.modules.users.domain.value_objects.password import Password


# ─── Валидные ──────────────────────────────────────────
def test_valid_password() -> None:
    password = Password("SecurePass123")
    assert password.value == "SecurePass123"


def test_min_length_boundary() -> None:
    # 8 символов, есть буква и цифра
    Password("Pass1234")


def test_max_length_boundary() -> None:
    # 128 символов, есть буква и цифра
    Password("a" + "1" * 126 + "b")


# ─── Длина ─────────────────────────────────────────────
def test_too_short_raises() -> None:
    with pytest.raises(InvalidPasswordError):
        Password("Pass123")  # 7 символов


def test_too_long_raises() -> None:
    with pytest.raises(InvalidPasswordError):
        Password("a" * 128 + "1")  # 129 символов


# ─── Сложность ─────────────────────────────────────────
def test_no_letter_raises() -> None:
    with pytest.raises(InvalidPasswordError):
        Password("12345678")


def test_no_digit_raises() -> None:
    with pytest.raises(InvalidPasswordError):
        Password("password")


# ─── Иммутабельность ───────────────────────────────────
def test_immutable() -> None:
    password = Password("SecurePass123")
    with pytest.raises(FrozenInstanceError):
        password.value = "other"  # type: ignore[misc]


# ─── Равенство по значению ─────────────────────────────
def test_equality_by_value() -> None:
    assert Password("SecurePass123") == Password("SecurePass123")
    assert Password("SecurePass123") != Password("OtherPass456")


def test_hash_by_value() -> None:
    assert hash(Password("SecurePass123")) == hash(Password("SecurePass123"))


# ─── Маскировка ────────────────────────────────────────
def test_repr_masked() -> None:
    password = Password("SecurePass123")
    assert repr(password) == "Password(***)"
    assert "SecurePass123" not in repr(password)
