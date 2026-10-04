import re
from dataclasses import dataclass

from app.modules.users.domain.exceptions import InvalidFullNameError

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class FullName:
    """Full name of the user."""

    value: str

    def __post_init__(self) -> None:
        cleaned = _WHITESPACE.sub(" ", self.value).strip()
        if not cleaned:
            raise InvalidFullNameError("Full name must not be empty")
        if len(cleaned) > 200:
            raise InvalidFullNameError("Full name must not be longer than 200 characters")
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value
