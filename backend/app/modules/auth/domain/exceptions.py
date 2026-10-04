from app.core.domain.exceptions import DomainError


class InvalidTokenError(DomainError):
    """Token is malformed or has invalid signature."""


class TokenExpiredError(InvalidTokenError):
    """Token has expired."""


class TokenRevokedError(InvalidTokenError):
    """Token has been revoked (logout, rotation)."""


class InvalidCredentialsError(DomainError):
    """Login failed: unknown user, wrong password, or locked account."""
