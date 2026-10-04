from dataclasses import FrozenInstanceError

import pytest

from app.modules.users.domain.exceptions import InvalidEmailError
from app.modules.users.domain.value_objects.email import Email


class TestNormalization:
    def test_lowercases_value(self) -> None:
        assert Email("User@Example.COM").value == "user@example.com"

    def test_strips_surrounding_whitespace(self) -> None:
        assert Email("  user@example.com  ").value == "user@example.com"

    def test_applies_both_rules(self) -> None:
        assert Email("  USER@EXAMPLE.COM  ").value == "user@example.com"


class TestValidation:
    @pytest.mark.parametrize(
        "value",
        [
            "user@example.com",
            "USER@EXAMPLE.COM",
            "first.last@sub.example.co.uk",
            "user+tag@example.com",
            "user_name@example.com",
            "a@b.co",
            "user@пример.рф",
            "a" * 64 + "@example.com",
        ],
    )
    def test_accepts_valid_email(self, value: str) -> None:
        assert Email(value).value == value.strip().lower()

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param("", id="empty"),
            pytest.param("plainaddress", id="no-at-sign"),
            pytest.param("@example.com", id="empty-local-part"),
            pytest.param("user@", id="empty-domain"),
            pytest.param("user@localhost", id="domain-without-dot"),
            pytest.param("user@@example.com", id="double-at-sign"),
            pytest.param("us er@example.com", id="space-in-local-part"),
            pytest.param("user@exa mple.com", id="space-in-domain"),
            pytest.param("user@example.com.", id="trailing-dot-in-domain"),
            pytest.param("user@.example.com", id="leading-dot-in-domain"),
            pytest.param("user@example..com", id="double-dot-in-domain"),
            pytest.param(".user@example.com", id="leading-dot-in-local-part"),
            pytest.param("user.@example.com", id="trailing-dot-in-local-part"),
            pytest.param("us..er@example.com", id="double-dot-in-local-part"),
            pytest.param("user@-example.com", id="label-starts-with-hyphen"),
            pytest.param("user@example-.com", id="label-ends-with-hyphen"),
            pytest.param("user@example.123", id="numeric-tld"),
            pytest.param("a" * 65 + "@example.com", id="local-part-too-long"),
            pytest.param("user@" + "b" * 64 + ".com", id="domain-label-too-long"),
            pytest.param(
                "a" * 64 + "@" + ".".join(["b" * 63] * 3) + ".com",
                id="email-too-long",
            ),
            pytest.param("user\x00@example.com", id="null-byte"),
            pytest.param("user\n@example.com", id="newline"),
        ],
    )
    def test_rejects_invalid_email(self, value: str) -> None:
        with pytest.raises(InvalidEmailError):
            Email(value)


class TestEquality:
    def test_equal_by_normalized_value(self) -> None:
        assert Email("User@Example.com") == Email("user@example.com")

    def test_hash_equal_for_equal_values(self) -> None:
        assert hash(Email("A@B.com")) == hash(Email("a@b.com"))

    def test_different_values_are_not_equal(self) -> None:
        assert Email("a@b.com") != Email("c@d.com")

    def test_deduplicated_in_set(self) -> None:
        assert len({Email("A@B.com"), Email("a@b.com")}) == 1


class TestImmutability:
    def test_cannot_reassign_value(self) -> None:
        email = Email("user@example.com")
        with pytest.raises(FrozenInstanceError):
            email.value = "other@example.com"  # type: ignore[misc]


class TestStringRepresentation:
    def test_str_returns_value(self) -> None:
        assert str(Email("user@example.com")) == "user@example.com"
