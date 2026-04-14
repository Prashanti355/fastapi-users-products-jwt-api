import pytest


async def _get_me(async_client, headers):
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["resultado"]


@pytest.mark.asyncio
async def test_get_own_user_success(async_client, create_and_login_user):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    me = await _get_me(async_client, headers)

    response = await async_client.get(
        f"/api/v1/users/{me['id']}",
        headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] == 200
    assert body["resultado"]["id"] == me["id"]
    assert body["resultado"]["username"] == me["username"]


@pytest.mark.asyncio
async def test_get_user_without_token_returns_401(async_client, create_and_login_user):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    me = await _get_me(async_client, headers)

    response = await async_client.get(f"/api/v1/users/{me['id']}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_normal_user_cannot_list_all_users_returns_403(async_client, create_and_login_user):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    response = await async_client.get("/api/v1/users", headers=headers)

    assert response.status_code == 403
    body = response.json()
    assert body["codigo"] == 403


@pytest.mark.asyncio
async def test_superuser_can_list_all_users(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
):
    registration = await register_public_user()
    payload = registration["payload"]

    assert registration["response"].status_code == 201

    await promote_user_to_superuser(payload["username"])
    headers = await get_auth_headers(
        username=payload["username"],
        password=payload["password"]
    )

    response = await async_client.get("/api/v1/users", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] == 200
    assert "resultado" in body
    assert "data" in body["resultado"]


@pytest.mark.asyncio
async def test_normal_user_can_partial_update_own_non_privileged_fields(
    async_client,
    create_and_login_user,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    me = await _get_me(async_client, headers)

    response = await async_client.patch(
        f"/api/v1/users/{me['id']}",
        json={
            "occupation": "Investigadora",
            "address_city": "Queretaro"
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] == 200
    assert body["resultado"]["occupation"] == "Investigadora"
    assert body["resultado"]["address_city"] == "Queretaro"


@pytest.mark.asyncio
async def test_normal_user_cannot_modify_privileged_fields(
    async_client,
    create_and_login_user,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    me = await _get_me(async_client, headers)

    response = await async_client.patch(
        f"/api/v1/users/{me['id']}",
        json={"role": "admin"},
        headers=headers,
    )

    assert response.status_code == 403
    body = response.json()
    assert body["codigo"] == 403


@pytest.mark.asyncio
async def test_change_password_success(async_client, create_and_login_user, login_user):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]
    payload = auth_data["payload"]

    me = await _get_me(async_client, headers)

    response = await async_client.post(
        f"/api/v1/users/{me['id']}/change-password",
        json={
            "current_password": payload["password"],
            "new_password": "NuevaClave1234",
            "confirm_password": "NuevaClave1234"
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] == 200

    relogin = await login_user(
        username=payload["username"],
        password="NuevaClave1234"
    )

    assert relogin.status_code == 200
    relogin_body = relogin.json()
    assert "access_token" in relogin_body


@pytest.mark.asyncio
async def test_change_password_for_other_user_returns_403(
    async_client,
    create_and_login_user,
):
    auth_data_1 = await create_and_login_user()
    headers_1 = auth_data_1["headers"]

    auth_data_2 = await create_and_login_user()
    headers_2 = auth_data_2["headers"]

    me_2 = await _get_me(async_client, headers_2)

    response = await async_client.post(
        f"/api/v1/users/{me_2['id']}/change-password",
        json={
            "current_password": auth_data_2["payload"]["password"],
            "new_password": "NuevaClave1234",
            "confirm_password": "NuevaClave1234"
        },
        headers=headers_1,
    )

    assert response.status_code == 403
    body = response.json()
    assert body["codigo"] == 403


@pytest.mark.asyncio
async def test_superuser_can_create_user(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
    build_public_register_payload,
    unique_suffix,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]

    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"],
        password=admin_payload["password"]
    )

    public_payload = build_public_register_payload(unique_suffix)

    response = await async_client.post(
        "/api/v1/users",
        json={
            **public_payload,
            "is_active": True,
            "is_superuser": False,
            "role": "user",
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["codigo"] == 201
    assert body["resultado"]["username"] == public_payload["username"]

@pytest.mark.asyncio
async def test_superuser_can_deactivate_and_activate_user(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"],
        password=admin_payload["password"]
    )

    target_registration = await register_public_user()
    target_payload = target_registration["payload"]
    assert target_registration["response"].status_code == 201

    target_headers = await get_auth_headers(
        username=target_payload["username"],
        password=target_payload["password"]
    )
    target_me = await _get_me(async_client, target_headers)

    deactivate_response = await async_client.patch(
        f"/api/v1/users/{target_me['id']}/deactivate",
        headers=admin_headers,
    )

    assert deactivate_response.status_code == 200
    deactivate_body = deactivate_response.json()
    assert deactivate_body["codigo"] == 200
    assert deactivate_body["resultado"]["is_active"] is False

    activate_response = await async_client.patch(
        f"/api/v1/users/{target_me['id']}/activate",
        headers=admin_headers,
    )

    assert activate_response.status_code == 200
    activate_body = activate_response.json()
    assert activate_body["codigo"] == 200
    assert activate_body["resultado"]["is_active"] is True


@pytest.mark.asyncio
async def test_superuser_can_delete_and_restore_user(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"],
        password=admin_payload["password"]
    )

    target_registration = await register_public_user()
    target_payload = target_registration["payload"]
    assert target_registration["response"].status_code == 201

    target_headers = await get_auth_headers(
        username=target_payload["username"],
        password=target_payload["password"]
    )
    target_me = await _get_me(async_client, target_headers)

    delete_response = await async_client.delete(
        f"/api/v1/users/{target_me['id']}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 200
    delete_body = delete_response.json()
    assert delete_body["codigo"] == 200
    assert delete_body["resultado"]["is_deleted"] is True

    restore_response = await async_client.patch(
        f"/api/v1/users/{target_me['id']}/restore",
        headers=admin_headers,
    )

    assert restore_response.status_code == 200
    restore_body = restore_response.json()
    assert restore_body["codigo"] == 200
    assert restore_body["resultado"]["is_deleted"] is False