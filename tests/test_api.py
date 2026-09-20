async def test_health_check(client):
    response = await client.get("/")
    assert response.status_code == 200

async def test_create_user(client):
    response = await client.post(
        "/users",
        json={"email": "lucas@test.com", "password": "senha1234"},
    )
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "lucas@test.com"
    assert "password" not in data
    assert "hashed_password" not in data

async def test_list_assets_requires_auth(client):
    response = await client.get("/assets")
    assert response.status_code == 401

async def test_list_assets_with_auth(authenticated_client):
    response = await authenticated_client.get("/assets")
    assert response.status_code == 200

async def test_user_cannot_access_another_users_transaction(authenticated_client):
    
    client = authenticated_client
    
    asset_response = await client.post(
        "/assets",
        json={"ticker": "PETR4", "company_name": "Petrobras"},
    )
    asset_id = asset_response.json()["id"]
    
    transaction_response = await client.post(
        "/transactions",
        json={
            "asset_id": asset_id,
            "operation": "buy",
            "quantity": 10,
            "unitary_price": "30.00",
            "operation_date": "2026-01-15",
        },
    )
    transaction_id = transaction_response.json()["id"]
    
    email = "intruder@test.com"
    password = "senha1234"
    
    await client.post(
        "/users",
        json={"email": email, "password": password},
        headers={"Authorization": ""},
    )
    
    login_response = await client.post(
        "/login",
        data={"username": email, "password": password},
    )
    intruder_token = login_response.json()["access_token"]
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
    
    get_response = await client.get(
        f"/transactions/{transaction_id}",
        headers=intruder_headers,
    )
    assert get_response.status_code == 404
    
    patch_response = await client.patch(
        f"/transactions/{transaction_id}",
        json={"quantity": 999},
        headers=intruder_headers,
    )
    assert patch_response.status_code == 404
    
    delete_response = await client.delete(
        f"/transactions/{transaction_id}",
        headers=intruder_headers,
    )
    assert delete_response.status_code == 404
    
    owner_response = await client.get(f"/transactions/{transaction_id}")
    assert owner_response.status_code == 200
    assert owner_response.json()["quantity"] == 10