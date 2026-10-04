from app.core.domain.exceptions import (
    AlreadyExistsError,
    InvalidDataError,
)


class InvalidFullNameError(InvalidDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidEmailError(InvalidDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class EmailAlreadyTakenError(AlreadyExistsError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidPasswordError(InvalidDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
