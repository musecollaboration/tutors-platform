from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.domain.exceptions import (
    AlreadyExistsError,
    DomainError,
    InvalidDataError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitExceededError,
    UnauthorizedError,
)

# Порядок важен: от частных к общим (isinstance идёт сверху вниз)
_STATUS_MAP: list[tuple[type[DomainError], int]] = [
    (UnauthorizedError, 401),
    (RateLimitExceededError, 429),
    (NotFoundError, 404),
    (AlreadyExistsError, 409),
    (PermissionDeniedError, 403),
    (InvalidDataError, 422),
    (DomainError, 400),
]


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status = next(code for cls, code in _STATUS_MAP if isinstance(exc, cls))
        return JSONResponse(status_code=status, content={"detail": str(exc)})
