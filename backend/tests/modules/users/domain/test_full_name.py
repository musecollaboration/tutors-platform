from dataclasses import FrozenInstanceError

import pytest

from app.modules.users.domain.exceptions import InvalidFullNameError
from app.modules.users.domain.value_objects.full_name import FullName


class TestNormalization:
    def test_strips_surrounding_whitespace(self) -> None:
        assert FullName("  Иван Иванов  ").value == "Иван Иванов"

    def test_collapses_inner_whitespace(self) -> None:
        assert FullName("Иван    Иванов").value == "Иван Иванов"

    def test_collapses_tabs_and_newlines(self) -> None:
        assert FullName("Иван" + "	\n" + "Иванов").value == "Иван Иванов"


class TestValidation:
    @pytest.mark.parametrize(
        "value",
        [
            "Иван Иванов",
            "A",
            "Иван",
            "Иван  Иванов",
            "a" * 200,
        ],
    )
    def test_accepts_valid_full_name(self, value: str) -> None:
        assert FullName(value).value

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param("", id="empty"),
            pytest.param("   ", id="spaces-only"),
            pytest.param("	\n", id="whitespace-chars-only"),
            pytest.param("a" * 201, id="too-long"),
        ],
    )
    def test_rejects_invalid_full_name(self, value: str) -> None:
        with pytest.raises(InvalidFullNameError):
            FullName(value)


class TestEquality:
    def test_equal_by_normalized_value(self) -> None:
        assert FullName("Иван   Иванов") == FullName("  Иван Иванов ")

    def test_hash_equal_for_equal_values(self) -> None:
        assert hash(FullName("Иван  Иванов")) == hash(FullName("Иван Иванов"))

    def test_different_values_are_not_equal(self) -> None:
        assert FullName("Иван Иванов") != FullName("Пётр Петров")


class TestImmutability:
    def test_cannot_reassign_value(self) -> None:
        full_name = FullName("Иван Иванов")
        with pytest.raises(FrozenInstanceError):
            full_name.value = "Пётр Петров"  # type: ignore[misc]


class TestStringRepresentation:
    def test_str_returns_value(self) -> None:
        assert str(FullName("Иван Иванов")) == "Иван Иванов"
