from app.core.domain.exceptions import NotFoundError, UnauthorizedError


class InvalidTokenError(UnauthorizedError):
    """Token is malformed or has invalid signature."""


class TokenExpiredError(InvalidTokenError):
    """Token has expired."""


class TokenRevokedError(InvalidTokenError):
    """Token has been revoked (logout, rotation)."""


class InvalidCredentialsError(UnauthorizedError):
    """Login failed: unknown user, wrong password, or locked account."""


class RefreshTokenNotFoundError(NotFoundError):
    """Refresh token does not exist."""
