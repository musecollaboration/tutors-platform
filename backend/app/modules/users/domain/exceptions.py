from app.core.domain.exceptions import (
    AlreadyExistsError,
    InvalidDataError,
)


class InvalidFullNameError(InvalidDataError):
    """Full name failed validation."""


class InvalidEmailError(InvalidDataError):
    """Email failed validation."""


class EmailAlreadyTakenError(AlreadyExistsError):
    """Account with the same email already exists."""


class InvalidPasswordError(InvalidDataError):
    """Password failed validation."""
