import hashlib
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import jwt
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError as JwtInvalidTokenError

from app.modules.auth.domain.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)
from app.modules.auth.domain.value_objects.token_payload import TokenPayload


class JwtTokenService:
    """JWT operations backed by PyJWT (HS256)."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_expire_minutes: int,
        refresh_expire_days: int,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expire_minutes = access_expire_minutes
        self._refresh_expire_days = refresh_expire_days

    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._access_expire_minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: UUID) -> tuple[str, datetime]:
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self._refresh_expire_days)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token, expires_at

    def decode(
        self,
        token: str,
        expected_type: Literal["access", "refresh"],
    ) -> TokenPayload:
        try:
            raw = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except ExpiredSignatureError as exc:
            raise TokenExpiredError("Token has expired") from exc
        except JwtInvalidTokenError as exc:
            raise InvalidTokenError("Token is invalid") from exc

        if raw.get("type") != expected_type:
            raise InvalidTokenError(f"Expected token type '{expected_type}'")

        try:
            sub = UUID(raw["sub"])
            iat = datetime.fromtimestamp(raw["iat"], tz=UTC)
            exp = datetime.fromtimestamp(raw["exp"], tz=UTC)
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError("Token payload is malformed") from exc

        return TokenPayload(sub=sub, type=expected_type, exp=exp, iat=iat)

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
