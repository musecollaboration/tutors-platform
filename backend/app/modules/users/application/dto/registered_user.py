from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.users.domain.value_objects.email import Email


@dataclass(frozen=True, slots=True)
class RegisteredUser:
    """Registration result: user data plus credentials."""

    id: UUID
    full_name: str
    email: Email
    is_active: bool
    created_at: datetime
