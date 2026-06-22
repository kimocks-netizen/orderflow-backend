from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    res = client.post("/api/auth/login", json={"email": "admin@orderflow.com", "password": "password"})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["user"]["email"] == "admin@orderflow.com"


def test_login_wrong_password(client: TestClient):
    res = client.post("/api/auth/login", json={"email": "admin@orderflow.com", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_email(client: TestClient):
    res = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "password"})
    assert res.status_code == 401


def test_protected_route_without_token(client: TestClient):
    res = client.get("/api/orders")
    assert res.status_code == 401


def test_protected_route_invalid_token(client: TestClient):
    res = client.get("/api/orders", headers={"Authorization": "Bearer bad-token"})
    assert res.status_code == 401
