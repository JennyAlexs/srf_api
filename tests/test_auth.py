import pytest
from fastapi.testclient import TestClient
from main import app
from dependencies import require_role
from main import check_client_role
from dependencies import get_current_user

client = TestClient(app)

# 1. Фикстура для получения валидного токена
@pytest.fixture
def client_token():
    resp = client.post("/auth/login", data={"username": "test_client", "password": "secure123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]

# 2. Тест успешного логина
def test_login_success():
    resp = client.post("/auth/login", data={"username": "test_client", "password": "secure123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"

# 3. Тест неверного пароля
def test_login_wrong_password():
    resp = client.post("/auth/login", data={"username": "test_client", "password": "wrong"})
    assert resp.status_code == 401
    assert "detail" in resp.json()

# 4. Доступ к защищённому маршруту без токена
def test_bookings_without_token():
    resp = client.post("/bookings/", json={"user_id": 1, "facility_id": 1})
    assert resp.status_code == 401

# 5. Доступ с валидным токеном
def test_bookings_with_valid_token(client_token):
    resp = client.post(
        "/bookings/",
        json={"user_id": 1, "facility_id": 1},
        headers={"Authorization": f"Bearer {client_token}"}
    )
    assert resp.status_code in (200, 201, 400, 404)

# 6. Проверка блокировки при несовпадении роли
def test_wrong_role_returns_403(client_token):
    app.dependency_overrides[get_current_user] = lambda: {"user_id": 1, "role": "admin"}
    
    resp = client.post(
        "/bookings/",
        json={"user_id": 1, "facility_id": 1},
        headers={"Authorization": f"Bearer {client_token}"}
    )
    
    assert resp.status_code == 403
    
    app.dependency_overrides.clear()