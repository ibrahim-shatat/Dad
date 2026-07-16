"""Tests for M8: user management, audit logging, the admin health view, and the rate limiter."""

import time

import pytest
from fastapi import HTTPException

from app.core.ratelimit import RateLimiter, _hits
from app.models.user import UserRole


async def _admin_headers(make_user):
    from app.core.security import create_access_token

    admin = await make_user(role=UserRole.admin)
    return admin, {"Authorization": f"Bearer {create_access_token(admin.id)}"}


async def test_non_admin_cannot_list_users(client, auth_user):
    _, headers = auth_user  # a director, not admin
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 403


async def test_admin_can_create_and_update_users(client, make_user):
    _, headers = await _admin_headers(make_user)

    created = await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "newbie@example.com",
            "password": "temp-pass-123",
            "full_name": "New Bie",
            "role": "assistant",
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    promoted = await client.patch(
        f"/api/v1/users/{user_id}", headers=headers, json={"role": "director"}
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "director"

    deactivated = await client.patch(
        f"/api/v1/users/{user_id}", headers=headers, json={"is_active": False}
    )
    assert deactivated.json()["is_active"] is False


async def test_admin_cannot_lock_themselves_out(client, make_user):
    admin, headers = await _admin_headers(make_user)

    demote = await client.patch(
        f"/api/v1/users/{admin.id}", headers=headers, json={"role": "assistant"}
    )
    assert demote.status_code == 400

    deactivate = await client.patch(
        f"/api/v1/users/{admin.id}", headers=headers, json={"is_active": False}
    )
    assert deactivate.status_code == 400


async def test_login_and_failure_are_audited(client, make_user):
    admin, headers = await _admin_headers(make_user)
    await make_user(email="real@example.com", password="correct-horse")

    # A bad login and a good one.
    await client.post(
        "/api/v1/auth/login",
        data={"username": "real@example.com", "password": "wrong"},
    )
    await client.post(
        "/api/v1/auth/login",
        data={"username": "real@example.com", "password": "correct-horse"},
    )

    audit = await client.get("/api/v1/admin/audit", headers=headers)
    assert audit.status_code == 200
    actions = {e["action"] for e in audit.json()}
    assert "auth.login" in actions
    assert "auth.login_failed" in actions


async def test_health_reports_counts(client, make_user):
    _, headers = await _admin_headers(make_user)
    resp = await client.get("/api/v1/admin/health", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_users"] >= 1
    assert body["failed_documents"] == 0
    assert body["connected_accounts"] == []


async def test_rate_limiter_blocks_after_limit(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    _hits.clear()
    limiter = RateLimiter(limit=3, window_seconds=60, scope="test")

    class _Req:
        headers: dict = {}
        client = type("C", (), {"host": "1.2.3.4"})()

    req = _Req()
    for _ in range(3):
        await limiter(req)  # first 3 allowed
    with pytest.raises(HTTPException) as exc:
        await limiter(req)
    assert exc.value.status_code == 429
    assert time.monotonic()  # sanity
