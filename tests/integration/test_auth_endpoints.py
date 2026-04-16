import pytest


@pytest.mark.asyncio
async def test_register_success(async_client, register_public_user):
    result = await register_public_user()
    response = result["response"]

    assert response.status_code == 201

    body = response.json()
    assert body["codigo"] == 201
    assert "resultado" in body
    assert "access_token" in body["resultado"]
    assert "refresh_token" in body["resultado"]
    assert body["resultado"]["token_type"] == "bearer"
    assert body["resultado"]["expires_in"] > 0


@pytest.mark.asyncio
async def test_register_duplicate_user_returns_conflict(async_client, register_public_user):
    first = await register_public_user()
    payload = first["payload"]

    assert first["response"].status_code == 201

    second_response = await async_client.post(
        "/api/v1/auth/register",
        json=payload
    )

    assert second_response.status_code == 409

    body = second_response.json()
    assert body["codigo"] == 409


@pytest.mark.asyncio
async def test_login_success(async_client, register_public_user, login_user):
    registration = await register_public_user()
    payload = registration["payload"]

    assert registration["response"].status_code == 201

    response = await login_user(
        username=payload["username"],
        password=payload["password"]
    )

    assert response.status_code == 200

    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_with_invalid_password_returns_401(async_client, register_public_user, login_user):
    registration = await register_public_user()
    payload = registration["payload"]

    assert registration["response"].status_code == 201

    response = await login_user(
        username=payload["username"],
        password="PasswordIncorrecto999"
    )

    assert response.status_code == 401

    body = response.json()
    assert body["codigo"] == 401


@pytest.mark.asyncio
async def test_me_with_valid_token_returns_current_user(
    async_client,
    create_and_login_user,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]
    payload = auth_data["payload"]

    response = await async_client.get(
        "/api/v1/auth/me",
        headers=headers
    )

    assert response.status_code == 200

    body = response.json()
    assert body["codigo"] == 200
    assert body["resultado"]["username"] == payload["username"]
    assert body["resultado"]["email"] == payload["email"]
    assert body["resultado"]["is_superuser"] is False
    assert body["resultado"]["is_active"] is True


@pytest.mark.asyncio
async def test_me_without_token_returns_401(async_client):
    response = await async_client.get("/api/v1/auth/me")

    assert response.status_code == 401

    body = response.json()
    assert "detail" in body


@pytest.mark.asyncio
async def test_refresh_token_success(async_client, register_public_user):
    registration = await register_public_user()
    response = registration["response"]

    assert response.status_code == 201

    refresh_token = response.json()["resultado"]["refresh_token"]

    refresh_response = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": refresh_token}
    )

    assert refresh_response.status_code == 200

    body = refresh_response.json()
    assert body["codigo"] == 200
    assert "access_token" in body["resultado"]
    assert "refresh_token" in body["resultado"]
    assert body["resultado"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_with_invalid_token_returns_401(async_client):
    response = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": "token.invalido.de.prueba"}
    )

    assert response.status_code == 401

    body = response.json()
    assert body["codigo"] == 401


@pytest.mark.asyncio
async def test_public_register_does_not_create_superuser(
    async_client,
    register_public_user,
    login_user,
):
    registration = await register_public_user()
    payload = registration["payload"]

    assert registration["response"].status_code == 201

    login_response = await login_user(
        username=payload["username"],
        password=payload["password"]
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert me_response.status_code == 200

    body = me_response.json()
    assert body["resultado"]["username"] == payload["username"]
    assert body["resultado"]["is_superuser"] is False

@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(async_client, register_public_user):
    registration = await register_public_user()
    payload = registration["payload"]

    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["username"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    logout_response = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 200
    logout_body = logout_response.json()
    assert logout_body["codigo"] == 200
    assert logout_body["mensaje"] == "Sesión cerrada exitosamente."

    refresh_response = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401    

@pytest.mark.asyncio
async def test_logout_is_idempotent(async_client, register_public_user, login_user):
    registration = await register_public_user()
    payload = registration["payload"]

    login_response = await login_user(
        username=payload["username"],
        password=payload["password"],
    )

    assert login_response.status_code == 200
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    first_logout = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert first_logout.status_code == 200
    first_body = first_logout.json()
    assert first_body["codigo"] == 200
    assert first_body["mensaje"] == "Sesión cerrada exitosamente."

    second_logout = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert second_logout.status_code == 200
    second_body = second_logout.json()
    assert second_body["codigo"] == 200
    assert second_body["mensaje"] == "Sesión cerrada exitosamente."


@pytest.mark.asyncio
async def test_refresh_token_rotation_invalidates_old_refresh_token(
    async_client,
    register_public_user,
    login_user,
):
    registration = await register_public_user()
    payload = registration["payload"]

    login_response = await login_user(
        username=payload["username"],
        password=payload["password"],
    )

    assert login_response.status_code == 200
    login_tokens = login_response.json()
    old_refresh_token = login_tokens["refresh_token"]

    first_refresh = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": old_refresh_token},
    )

    assert first_refresh.status_code == 200
    first_refresh_body = first_refresh.json()
    new_refresh_token = first_refresh_body["resultado"]["refresh_token"]

    reuse_old_refresh = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": old_refresh_token},
    )

    assert reuse_old_refresh.status_code == 401

    use_new_refresh = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": new_refresh_token},
    )

    assert use_new_refresh.status_code == 200


@pytest.mark.asyncio
async def test_logout_revoked_refresh_token_cannot_be_used_again(
    async_client,
    register_public_user,
    login_user,
):
    registration = await register_public_user()
    payload = registration["payload"]

    login_response = await login_user(
        username=payload["username"],
        password=payload["password"],
    )

    assert login_response.status_code == 200
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    logout_response = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 200

    refresh_after_logout = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": refresh_token},
    )

    assert refresh_after_logout.status_code == 401    

@pytest.mark.asyncio
async def test_logout_all_revokes_all_refresh_tokens_for_current_user(
    async_client,
    register_public_user,
    login_user,
):
    registration = await register_public_user()
    payload = registration["payload"]

    first_login = await login_user(
        username=payload["username"],
        password=payload["password"],
    )
    assert first_login.status_code == 200
    first_tokens = first_login.json()

    second_login = await login_user(
        username=payload["username"],
        password=payload["password"],
    )
    assert second_login.status_code == 200
    second_tokens = second_login.json()

    access_token = second_tokens["access_token"]

    logout_all_response = await async_client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert logout_all_response.status_code == 200
    logout_all_body = logout_all_response.json()
    assert logout_all_body["codigo"] == 200
    assert logout_all_body["mensaje"] == "Todas las sesiones fueron cerradas exitosamente."

    first_refresh_after_logout_all = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": first_tokens["refresh_token"]},
    )
    assert first_refresh_after_logout_all.status_code == 401

    second_refresh_after_logout_all = await async_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": second_tokens["refresh_token"]},
    )
    assert second_refresh_after_logout_all.status_code == 401    