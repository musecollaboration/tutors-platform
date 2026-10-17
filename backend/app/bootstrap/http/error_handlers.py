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

# Категории: core-тип → HTTP-статус. Порядок не важен: поиск идёт по __mro__,
# который сам выдаёт частные классы раньше общих.
_STATUS_MAP: dict[type[DomainError], int] = {
    UnauthorizedError: 401,
    RateLimitExceededError: 429,
    NotFoundError: 404,
    AlreadyExistsError: 409,
    PermissionDeniedError: 403,
    InvalidDataError: 422,
    DomainError: 400,
}

# Недостижимо, пока DomainError есть в _STATUS_MAP: страховка от его удаления.
_FALLBACK_STATUS = 500


def _status_for(exc: DomainError) -> int:
    """Resolve HTTP status by walking the MRO from specific classes to general."""
    for cls in type(exc).__mro__:
        if cls in _STATUS_MAP:
            return _STATUS_MAP[cls]
    return _FALLBACK_STATUS


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=_status_for(exc), content={"detail": str(exc)})


# # Старая реализация поиска статуса по типу исключения.
# # Оставил для примера так как в видео уроке начинали с данной реализации.
# _STATUS_MAP: list[tuple[type[DomainError], int]] = [
#     (UnauthorizedError, 401),
#     (RateLimitExceededError, 429),
#     (NotFoundError, 404),
#     (AlreadyExistsError, 409),
#     (PermissionDeniedError, 403),
#     (InvalidDataError, 422),
#     (DomainError, 400),
# ]


# def register_error_handlers(app: FastAPI) -> None:
#     """Register global exception handlers."""

#     @app.exception_handler(DomainError)
#     async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
#         status = next(code for cls, code in _STATUS_MAP if isinstance(exc, cls))
#         return JSONResponse(status_code=status, content={"detail": str(exc)})
