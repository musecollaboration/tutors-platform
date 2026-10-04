class DomainError(Exception):
    """Base class for all domain errors."""


class NotFoundError(DomainError):
    """Requested entity does not exist."""


class AlreadyExistsError(DomainError):
    """Entity with the same unique attribute already exists."""


class PermissionDeniedError(DomainError):
    """Current actor is not allowed to perform the action."""


class InvalidDataError(DomainError):
    """Domain invariant or input validation failed."""


class RateLimitExceededError(DomainError):
    """Rate limit exceeded."""
