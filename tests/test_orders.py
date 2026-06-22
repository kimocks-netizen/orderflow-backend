from fastapi.testclient import TestClient


def _create(client, headers, name="Jane Doe", email="jane@example.com", amount=99.99):
    res = client.post(
        "/api/orders",
        json={"customer_name": name, "customer_email": email, "total_amount": amount},
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()


def test_create_order(client: TestClient, auth_headers):
    order = _create(client, auth_headers)
    assert order["status"] == "pending"
    assert order["customer_name"] == "Jane Doe"
    assert order["total_amount"] == 99.99


def test_create_order_invalid_email(client: TestClient, auth_headers):
    res = client.post(
        "/api/orders",
        json={"customer_name": "Jane", "customer_email": "not-an-email", "total_amount": 10},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_create_order_negative_amount(client: TestClient, auth_headers):
    res = client.post(
        "/api/orders",
        json={"customer_name": "Jane", "customer_email": "jane@example.com", "total_amount": -1},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_create_order_missing_name(client: TestClient, auth_headers):
    res = client.post(
        "/api/orders",
        json={"customer_name": "", "customer_email": "jane@example.com", "total_amount": 10},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_get_order(client: TestClient, auth_headers):
    order = _create(client, auth_headers)
    res = client.get(f"/api/orders/{order['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == order["id"]


def test_get_order_not_found(client: TestClient, auth_headers):
    res = client.get("/api/orders/99999", headers=auth_headers)
    assert res.status_code == 404


def test_list_orders_pagination(client: TestClient, auth_headers):
    for i in range(5):
        _create(client, auth_headers, email=f"user{i}@example.com")
    res = client.get("/api/orders?page=1&page_size=3", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) == 3
    assert body["total"] >= 5
    assert body["total_pages"] >= 2


def test_list_orders_filter_by_status(client: TestClient, auth_headers):
    _create(client, auth_headers, email="pending@example.com")
    res = client.get("/api/orders?status=pending", headers=auth_headers)
    assert res.status_code == 200
    assert all(o["status"] == "pending" for o in res.json()["items"])


def test_list_orders_search(client: TestClient, auth_headers):
    _create(client, auth_headers, name="Unique SearchName", email="unique@example.com")
    res = client.get("/api/orders?search=SearchName", headers=auth_headers)
    assert res.status_code == 200
    assert any("SearchName" in o["customer_name"] for o in res.json()["items"])


def test_order_history_created_on_new_order(client: TestClient, auth_headers):
    order = _create(client, auth_headers)
    res = client.get(f"/api/orders/{order['id']}/history", headers=auth_headers)
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 1
    assert history[0]["to_status"] == "pending"
    assert history[0]["from_status"] is None
