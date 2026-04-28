import pytest


@pytest.mark.asyncio
async def test_audit_logs_without_token_returns_401(async_client):
    response = await async_client.get("/api/v1/audit-logs")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_normal_user_cannot_list_audit_logs(
    async_client,
    register_public_user,
    get_auth_headers,
):
    registration = await register_public_user()
    payload = registration["payload"]

    assert registration["response"].status_code == 201

    user_headers = await get_auth_headers(
        username=payload["username"],
        password=payload["password"],
    )

    response = await async_client.get(
        "/api/v1/audit-logs",
        headers=user_headers,
    )

    assert response.status_code == 403
    body = response.json()

    assert body["codigo"] == 403
    assert body["resultado"] is None


@pytest.mark.asyncio
async def test_superuser_can_list_audit_logs(
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
        password=admin_payload["password"],
    )

    response = await async_client.get(
        "/api/v1/audit-logs?page=1&limit=10&sort_by=created_at&order=desc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["codigo"] == 200
    assert body["mensaje"] == "Logs de auditoría obtenidos correctamente."
    assert "resultado" in body

    resultado = body["resultado"]
    assert "total" in resultado
    assert "page" in resultado
    assert "limit" in resultado
    assert "data" in resultado

    assert resultado["page"] == 1
    assert resultado["limit"] == 10
    assert isinstance(resultado["data"], list)
    assert resultado["total"] >= 1

    first_item = resultado["data"][0]
    expected_keys = {
        "id",
        "action",
        "entity",
        "entity_id",
        "actor_id",
        "actor_username",
        "actor_role",
        "request_id",
        "status",
        "detail",
        "created_at",
    }

    assert expected_keys.issubset(first_item.keys())


@pytest.mark.asyncio
async def test_superuser_can_filter_audit_logs_by_action(
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
        password=admin_payload["password"],
    )

    response = await async_client.get(
        "/api/v1/audit-logs?action=login&page=1&limit=20&sort_by=created_at&order=desc",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["codigo"] == 200

    data = body["resultado"]["data"]
    assert isinstance(data, list)
    assert len(data) >= 1

    for item in data:
        assert item["action"] == "login"


@pytest.mark.asyncio
async def test_superuser_can_filter_audit_logs_by_request_id(
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
        password=admin_payload["password"],
    )

    list_response = await async_client.get(
        "/api/v1/audit-logs?page=1&limit=20&sort_by=created_at&order=desc",
        headers=admin_headers,
    )

    assert list_response.status_code == 200

    list_body = list_response.json()
    data = list_body["resultado"]["data"]

    assert len(data) >= 1

    target_request_id = data[0]["request_id"]
    assert target_request_id is not None

    filtered_response = await async_client.get(
        f"/api/v1/audit-logs?request_id={target_request_id}",
        headers=admin_headers,
    )

    assert filtered_response.status_code == 200

    filtered_body = filtered_response.json()
    filtered_data = filtered_body["resultado"]["data"]

    assert len(filtered_data) >= 1

    for item in filtered_data:
        assert item["request_id"] == target_request_id
