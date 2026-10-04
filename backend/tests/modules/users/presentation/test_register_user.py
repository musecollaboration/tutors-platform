import httpx

USERS_URL = "/api/v1/users"


def _payload(
    full_name: str = "Иван Иванов",
    email: str = "ivan@example.com",
    password: str = "secret123",
) -> dict[str, str]:
    return {"full_name": full_name, "email": email, "password": password}


async def test_register_returns_201(client: httpx.AsyncClient) -> None:
    response = await client.post(USERS_URL, json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["email"] == "ivan@example.com"


async def test_register_response_shape(client: httpx.AsyncClient) -> None:
    response = await client.post(USERS_URL, json=_payload())

    assert response.status_code == 201
    assert set(response.json()) == {
        "id",
        "full_name",
        "email",
        "is_active",
        "created_at",
    }


async def test_register_duplicate_email_returns_409(client: httpx.AsyncClient) -> None:
    payload = _payload()

    first = await client.post(USERS_URL, json=payload)
    assert first.status_code == 201

    second = await client.post(USERS_URL, json=payload)
    assert second.status_code == 409


async def test_register_invalid_email_returns_422(client: httpx.AsyncClient) -> None:
    response = await client.post(USERS_URL, json=_payload(email="not-an-email"))

    assert response.status_code == 422


async def test_register_short_password_returns_422(client: httpx.AsyncClient) -> None:
    response = await client.post(USERS_URL, json=_payload(password="short1"))

    assert response.status_code == 422


async def test_health_returns_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
