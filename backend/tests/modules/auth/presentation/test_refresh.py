import httpx

REFRESH_URL = "/api/v1/auth/refresh"


async def test_refresh_with_invalid_token_returns_401(client: httpx.AsyncClient) -> None:
    response = await client.post(REFRESH_URL, json={"refresh_token": "not-a-valid-token"})

    assert response.status_code == 401
    # 401 приходит от глобального обработчика DomainError, а не от FastAPI.
    assert response.json() == {"detail": "Token is invalid"}
