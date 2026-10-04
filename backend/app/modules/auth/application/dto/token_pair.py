from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenPair:
    """Access + refresh token pair returned to the client."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
