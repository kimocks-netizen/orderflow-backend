import pytest
from fastapi.testclient import TestClient


def _create(client, headers, email="t@example.com"):
    res = client.post(
        "/api/orders",
        json={"customer_name": "Test User", "customer_email": email, "total_amount": 50.0},
        headers=headers,
    )
    return res.json()


def _patch(client, headers, order_id, status):
    return client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": status},
        headers=headers,
    )


# ── Valid transitions ─────────────────────────────────────────────────────────

def test_pending_to_paid(client: TestClient, auth_headers):
    order = _create(client, auth_headers, "p2p@example.com")
    res = _patch(client, auth_headers, order["id"], "paid")
    assert res.status_code == 200
    assert res.json()["status"] == "paid"


def test_pending_to_cancelled(client: TestClient, auth_headers):
    order = _create(client, auth_headers, "p2c@example.com")
    res = _patch(client, auth_headers, order["id"], "cancelled")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


def test_paid_to_shipped(client: TestClient, auth_headers):
    order = _create(client, auth_headers, "p2s@example.com")
    _patch(client, auth_headers, order["id"], "paid")
    res = _patch(client, auth_headers, order["id"], "shipped")
    assert res.status_code == 200
    assert res.json()["status"] == "shipped"


def test_paid_to_cancelled(client: TestClient, auth_headers):
    order = _create(client, auth_headers, "pc2c@example.com")
    _patch(client, auth_headers, order["id"], "paid")
    res = _patch(client, auth_headers, order["id"], "cancelled")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"


# ── Invalid transitions ───────────────────────────────────────────────────────

@pytest.mark.parametrize("from_status,to_status,setup_steps", [
    ("pending",   "shipped",  []),
    ("shipped",   "paid",     ["paid", "shipped"]),
    ("shipped",   "pending",  ["paid", "shipped"]),
    ("cancelled", "paid",     ["cancelled"]),
    ("cancelled", "pending",  ["cancelled"]),
])
def test_invalid_transition(client: TestClient, auth_headers, from_status, to_status, setup_steps):
    order = _create(client, auth_headers, f"{from_status}-{to_status}@example.com")
    for step in setup_steps:
        _patch(client, auth_headers, order["id"], step)
    res = _patch(client, auth_headers, order["id"], to_status)
    assert res.status_code == 400


# ── Terminal states ───────────────────────────────────────────────────────────

def test_shipped_is_terminal(client: TestClient, auth_headers):
    order = _create(client, auth_headers, "shipped-terminal@example.com")
    _patch(client, auth_headers, order["id"], "paid")
    _patch(client, auth_headers, order["id"], "shipped")
    for target in ["pending", "paid", "cancelled"]:
        res = _patch(client, auth_headers, order["id"], target)
        assert res.status_code == 400


def test_cancelled_is_terminal(client: TestClient, auth_headers):
    order = _create(client, auth_headers, "cancelled-terminal@example.com")
    _patch(client, auth_headers, order["id"], "cancelled")
    for target in ["pending", "paid", "shipped"]:
        res = _patch(client, auth_headers, order["id"], target)
        assert res.status_code == 400


# ── History audit trail ───────────────────────────────────────────────────────

def test_full_lifecycle_history(client: TestClient, auth_headers):
    order = _create(client, auth_headers, "history@example.com")
    oid = order["id"]
    _patch(client, auth_headers, oid, "paid")
    _patch(client, auth_headers, oid, "shipped")

    res = client.get(f"/api/orders/{oid}/history", headers=auth_headers)
    history = res.json()
    assert len(history) == 3
    assert history[0]["to_status"] == "pending"
    assert history[1]["from_status"] == "pending"
    assert history[1]["to_status"] == "paid"
    assert history[2]["from_status"] == "paid"
    assert history[2]["to_status"] == "shipped"
