from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.domain.exceptions import InvalidTokenError
from app.modules.users.public import UsersFacade, UserSummary

# auto_error=False: сами возвращаем 401 вместо FastAPI-шного 403.
_bearer_scheme = HTTPBearer(auto_error=False)


@inject
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    tokens: FromDishka[TokenService],
    users: FromDishka[UsersFacade],
) -> UserSummary:
    """Decode access token and resolve the current user.

    Raises InvalidTokenError when the token is missing or malformed.
    """
    if credentials is None:
        raise InvalidTokenError("Authorization header is missing")

    payload = tokens.decode(credentials.credentials, expected_type="access")

    user = await users.get_summary(payload.sub)
    if user is None or not user.is_active:
        raise InvalidTokenError("User is not active")

    return user


CurrentUser = Annotated[UserSummary, Depends(get_current_user)]
