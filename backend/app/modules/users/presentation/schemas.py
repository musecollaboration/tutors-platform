# presentation/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.modules.users.application.dto.registered_user import RegisteredUser


class RegisterUserRequest(BaseModel):
    """User registration request."""

    full_name: str = Field(
        min_length=1,
        max_length=200,
        description="Полное имя пользователя",
        examples=["Иван Иванов"],
    )
    email: EmailStr = Field(
        description="Email пользователя",
        examples=["ivan@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Пароль: минимум 8 символов, буквы и цифры",
        examples=["SecurePass123"],
    )


class RegisterUserResponse(BaseModel):
    """Reply with registered user details"""

    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: RegisteredUser) -> RegisterUserResponse:
        return cls(
            id=dto.id,
            full_name=dto.full_name,
            email=dto.email.value,
            is_active=dto.is_active,
            created_at=dto.created_at,
        )
