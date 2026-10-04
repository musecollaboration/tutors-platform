from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from app.modules.auth.application.use_cases.login import Login
from app.modules.auth.application.use_cases.logout import Logout
from app.modules.auth.application.use_cases.refresh import Refresh
from app.modules.auth.presentation.dependencies import CurrentUser
from app.modules.auth.presentation.schemas import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    use_case: FromDishka[Login],
) -> TokenResponse:
    """Вход по email и паролю. Возвращает пару access+refresh."""
    pair = await use_case.execute(email=body.email, password=body.password)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    use_case: FromDishka[Refresh],
) -> TokenResponse:
    """Обновление пары токенов по refresh. Старый refresh отзывается."""
    pair = await use_case.execute(refresh_token=body.refresh_token)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
    )


@router.post("/logout", status_code=204)
async def logout(
    body: LogoutRequest,
    use_case: FromDishka[Logout],
) -> None:
    """Выход. Отзывает refresh. Идемпотентен."""
    await use_case.execute(refresh_token=body.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser) -> MeResponse:
    """Профиль текущего пользователя."""
    return MeResponse.from_summary(user)
