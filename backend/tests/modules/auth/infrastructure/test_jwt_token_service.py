from uuid import uuid4

from app.modules.auth.infrastructure.adapters import JwtTokenService

# Ключ ≥ 32 байт: PyJWT иначе ругается InsecureKeyLengthWarning для HS256.
_TEST_SECRET = "test-secret-key-for-hs256-0123456789"


def _make_service() -> JwtTokenService:
    return JwtTokenService(
        secret_key=_TEST_SECRET,
        algorithm="HS256",
        access_expire_minutes=15,
        refresh_expire_days=30,
    )


def test_refresh_tokens_are_unique_for_same_user() -> None:
    service = _make_service()
    user_id = uuid4()

    token1, _ = service.create_refresh_token(user_id)
    token2, _ = service.create_refresh_token(user_id)

    assert token1 != token2
    assert service.hash_token(token1) != service.hash_token(token2)


def test_access_tokens_are_unique_for_same_user() -> None:
    service = _make_service()
    user_id = uuid4()

    token1 = service.create_access_token(user_id)
    token2 = service.create_access_token(user_id)

    assert token1 != token2
    assert service.hash_token(token1) != service.hash_token(token2)
