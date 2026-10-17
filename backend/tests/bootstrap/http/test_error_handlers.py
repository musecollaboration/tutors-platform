import pytest

from app.bootstrap.http.error_handlers import _status_for
from app.core.domain.exceptions import (
    AlreadyExistsError,
    DomainError,
    InvalidDataError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitExceededError,
    UnauthorizedError,
)
from app.modules.auth.domain.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    RefreshTokenNotFoundError,
    TokenExpiredError,
    TokenRevokedError,
)
from app.modules.users.domain.exceptions import (
    AccountNotFoundError,
    EmailAlreadyTakenError,
    InvalidEmailError,
    UserNotFoundError,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected"),
    [
        # Категории core.
        (UnauthorizedError, 401),
        (RateLimitExceededError, 429),
        (NotFoundError, 404),
        (AlreadyExistsError, 409),
        (PermissionDeniedError, 403),
        (InvalidDataError, 422),
        (DomainError, 400),
        # Конкретика модулей: статус берётся у категории.
        (InvalidTokenError, 401),
        (TokenExpiredError, 401),
        (TokenRevokedError, 401),
        (InvalidCredentialsError, 401),
        (RefreshTokenNotFoundError, 404),
        (UserNotFoundError, 404),
        (AccountNotFoundError, 404),
        (EmailAlreadyTakenError, 409),
        (InvalidEmailError, 422),
    ],
)
def test_status_for_maps_exception_to_expected_status(exc_cls: type[DomainError], expected: int) -> None:
    assert _status_for(exc_cls("x")) == expected


def test_status_for_walks_mro_from_specific_to_general() -> None:
    """Subclass of a mapped category resolves via that category, not via DomainError."""

    class CustomNotFoundError(NotFoundError):
        """Unmapped concrete error of some module."""

    assert _status_for(CustomNotFoundError("x")) == 404
