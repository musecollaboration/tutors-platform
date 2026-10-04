import re
from dataclasses import dataclass

from app.modules.users.domain.exceptions import InvalidPasswordError

_MIN_LENGTH = 8
_MAX_LENGTH = 128

_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


@dataclass(frozen=True, slots=True)
class Password:
    """Plain-text password. Validated on creation, never stored as-is."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < _MIN_LENGTH:
            raise InvalidPasswordError(f"Password must be at least {_MIN_LENGTH} characters")
        if len(self.value) > _MAX_LENGTH:
            raise InvalidPasswordError(f"Password must be at most {_MAX_LENGTH} characters")
        if not _HAS_LETTER.search(self.value):
            raise InvalidPasswordError("Password must contain at least one letter")
        if not _HAS_DIGIT.search(self.value):
            raise InvalidPasswordError("Password must contain at least one digit")

    def __repr__(self) -> str:
        return "Password(***)"
