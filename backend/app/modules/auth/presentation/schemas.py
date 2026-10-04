from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.modules.users.public import UserSummary


class LoginRequest(BaseModel):
    """Запрос на вход."""

    email: EmailStr = Field(
        description="Email пользователя",
        examples=["ivan@example.com"],
    )
    password: str = Field(
        min_length=1,
        description="Пароль",
        examples=["SecurePass123"],
    )


class TokenResponse(BaseModel):
    """Пара токенов."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Запрос на обновление пары токенов."""

    refresh_token: str = Field(
        min_length=1,
        description="Refresh-токен, полученный при входе",
    )


class LogoutRequest(BaseModel):
    """Запрос на выход."""

    refresh_token: str = Field(
        min_length=1,
        description="Refresh-токен для отзыва",
    )


class MeResponse(BaseModel):
    """Профиль текущего пользователя."""

    id: UUID
    full_name: str
    email: str
    is_active: bool

    @classmethod
    def from_summary(cls, user: UserSummary) -> MeResponse:
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
        )
