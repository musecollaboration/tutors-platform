from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TokenPayload:
    """Decoded JWT payload. Immutable value object."""

    sub: UUID
    type: Literal["access", "refresh"]
    exp: datetime
    iat: datetime
