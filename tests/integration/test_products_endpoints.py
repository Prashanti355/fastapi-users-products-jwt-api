import pytest


@pytest.mark.asyncio
async def test_public_can_list_products(async_client):
    response = await async_client.get("/api/v1/products")

    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] == 200
    assert "resultado" in body
    assert "data" in body["resultado"]


@pytest.mark.asyncio
async def test_public_cannot_create_product_without_token(async_client, build_product_payload):
    payload = build_product_payload("publicfail")

    response = await async_client.post(
        "/api/v1/products",
        json=payload,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_user_can_create_product(
    async_client,
    create_and_login_user,
    create_product,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    created = await create_product(headers=headers)
    response = created["response"]

    assert response.status_code == 201
    body = response.json()
    assert body["codigo"] == 201
    assert body["resultado"]["name"] == created["payload"]["name"]


@pytest.mark.asyncio
async def test_public_can_get_product_by_id(
    async_client,
    create_and_login_user,
    create_product,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    created = await create_product(headers=headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]

    response = await async_client.get(f"/api/v1/products/{product_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] == 200
    assert body["resultado"]["id"] == product_id


@pytest.mark.asyncio
async def test_authenticated_user_can_partial_update_product(
    async_client,
    create_and_login_user,
    create_product,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    created = await create_product(headers=headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]

    response = await async_client.patch(
        f"/api/v1/products/{product_id}",
        json={"price": 13999.99, "description": "Producto actualizado parcialmente"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] == 200
    assert body["resultado"]["price"] in [13999.99, "13999.99"]


@pytest.mark.asyncio
async def test_normal_user_cannot_activate_product_returns_403(
    async_client,
    create_and_login_user,
    create_product,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    created = await create_product(headers=headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]

    response = await async_client.patch(
        f"/api/v1/products/{product_id}/activate",
        headers=headers,
    )

    assert response.status_code == 403
    body = response.json()
    assert body["codigo"] == 403


@pytest.mark.asyncio
async def test_superuser_can_deactivate_and_activate_product(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
    create_product,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"], password=admin_payload["password"]
    )

    created = await create_product(headers=admin_headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]

    deactivate_response = await async_client.patch(
        f"/api/v1/products/{product_id}/deactivate",
        headers=admin_headers,
    )

    assert deactivate_response.status_code == 200
    deactivate_body = deactivate_response.json()
    assert deactivate_body["codigo"] == 200
    assert deactivate_body["resultado"]["status"] is False

    activate_response = await async_client.patch(
        f"/api/v1/products/{product_id}/activate",
        headers=admin_headers,
    )

    assert activate_response.status_code == 200
    activate_body = activate_response.json()
    assert activate_body["codigo"] == 200
    assert activate_body["resultado"]["status"] is True


@pytest.mark.asyncio
async def test_superuser_can_delete_and_restore_product(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
    create_product,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"], password=admin_payload["password"]
    )

    created = await create_product(headers=admin_headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]

    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 200
    delete_body = delete_response.json()
    assert delete_body["codigo"] == 200
    assert delete_body["resultado"]["is_deleted"] is True

    restore_response = await async_client.patch(
        f"/api/v1/products/{product_id}/restore",
        headers=admin_headers,
    )

    assert restore_response.status_code == 200
    restore_body = restore_response.json()
    assert restore_body["codigo"] == 200
    assert restore_body["resultado"]["is_deleted"] is False


@pytest.mark.asyncio
async def test_deleted_product_is_not_visible_in_public_get(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
    create_product,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"], password=admin_payload["password"]
    )

    created = await create_product(headers=admin_headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]

    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200

    public_get = await async_client.get(f"/api/v1/products/{product_id}")

    assert public_get.status_code == 404
    body = public_get.json()
    assert body["codigo"] == 404


@pytest.mark.asyncio
async def test_deleted_product_does_not_appear_in_public_list(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
    create_product,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"], password=admin_payload["password"]
    )

    created = await create_product(headers=admin_headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]
    product_name = created["response"].json()["resultado"]["name"]

    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200

    list_response = await async_client.get("/api/v1/products")
    assert list_response.status_code == 200

    body = list_response.json()
    items = body["resultado"]["data"]

    ids = [item["id"] for item in items]
    names = [item["name"] for item in items]

    assert product_id not in ids
    assert product_name not in names


@pytest.mark.asyncio
async def test_public_get_nonexistent_product_returns_404(async_client):
    response = await async_client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    body = response.json()
    assert body["codigo"] == 404


@pytest.mark.asyncio
async def test_authenticated_user_cannot_delete_product_returns_403(
    async_client,
    create_and_login_user,
    create_product,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    created = await create_product(headers=headers)
    assert created["response"].status_code == 201

    product_id = created["response"].json()["resultado"]["id"]

    response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=headers,
    )

    assert response.status_code == 403
    body = response.json()
    assert body["codigo"] == 403


@pytest.mark.asyncio
async def test_authenticated_user_cannot_restore_product_returns_403(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
    create_and_login_user,
    create_product,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"],
        password=admin_payload["password"],
    )

    created = await create_product(headers=admin_headers)
    assert created["response"].status_code == 201
    product_id = created["response"].json()["resultado"]["id"]

    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200

    user_auth = await create_and_login_user()
    user_headers = user_auth["headers"]

    restore_response = await async_client.patch(
        f"/api/v1/products/{product_id}/restore",
        headers=user_headers,
    )

    assert restore_response.status_code == 403
    body = restore_response.json()
    assert body["codigo"] == 403


@pytest.mark.asyncio
async def test_public_cannot_patch_product_without_token(
    async_client,
    create_and_login_user,
    create_product,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    created = await create_product(headers=headers)
    assert created["response"].status_code == 201
    product_id = created["response"].json()["resultado"]["id"]

    response = await async_client.patch(
        f"/api/v1/products/{product_id}",
        json={"price": 123.45},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_public_cannot_delete_product_without_token(
    async_client,
    create_and_login_user,
    create_product,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    created = await create_product(headers=headers)
    assert created["response"].status_code == 201
    product_id = created["response"].json()["resultado"]["id"]

    response = await async_client.delete(f"/api/v1/products/{product_id}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_partial_update_nonexistent_product_returns_404(
    async_client,
    create_and_login_user,
):
    auth_data = await create_and_login_user()
    headers = auth_data["headers"]

    response = await async_client.patch(
        "/api/v1/products/00000000-0000-0000-0000-000000000000",
        json={"price": 999.99},
        headers=headers,
    )

    assert response.status_code == 404
    body = response.json()
    assert body["codigo"] == 404


@pytest.mark.asyncio
async def test_superuser_get_deleted_product_by_id_returns_404(
    async_client,
    register_public_user,
    get_auth_headers,
    promote_user_to_superuser,
    create_product,
):
    admin_registration = await register_public_user()
    admin_payload = admin_registration["payload"]
    assert admin_registration["response"].status_code == 201

    await promote_user_to_superuser(admin_payload["username"])
    admin_headers = await get_auth_headers(
        username=admin_payload["username"],
        password=admin_payload["password"],
    )

    created = await create_product(headers=admin_headers)
    assert created["response"].status_code == 201
    product_id = created["response"].json()["resultado"]["id"]

    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200

    response = await async_client.get(
        f"/api/v1/products/{product_id}",
        headers=admin_headers,
    )

    assert response.status_code == 404
    body = response.json()
    assert body["codigo"] == 404


@pytest.mark.asyncio
async def test_restore_nonexistent_product_returns_404_for_superuser(
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

    response = await async_client.patch(
        "/api/v1/products/00000000-0000-0000-0000-000000000000/restore",
        headers=admin_headers,
    )

    assert response.status_code == 404
    body = response.json()
    assert body["codigo"] == 404
