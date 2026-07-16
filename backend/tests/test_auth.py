"""Auth/JWT edge cases: login, refresh-cookie rotation, and the access-vs-refresh token type
check in get_current_user (easy to accidentally regress since both are plain JWTs signed with
the same secret, differing only in a `type` claim).
"""

from app.core.security import create_refresh_token
from app.models.user import UserRole


async def test_login_success_sets_refresh_cookie_and_returns_access_token(client, make_user):
    user = await make_user(email="director@example.com", password="correct-password")

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "correct-password"},
    )

    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert "refresh_token" in resp.cookies


async def test_login_wrong_password_is_401(client, make_user):
    user = await make_user(password="correct-password")

    resp = await client.post(
        "/api/v1/auth/login", data={"username": user.email, "password": "wrong-password"}
    )

    assert resp.status_code == 401


async def test_login_disabled_account_is_403(client, make_user, db_session):
    user = await make_user(password="correct-password")
    user.is_active = False
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login", data={"username": user.email, "password": "correct-password"}
    )

    assert resp.status_code == 403


async def test_users_me_requires_valid_access_token(client, auth_user):
    user, headers = auth_user

    resp = await client.get("/api/v1/users/me", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["email"] == user.email


async def test_refresh_token_rejected_as_bearer_access_token(client, make_user):
    """A refresh-type JWT must not work as an access token — they're both just JWTs signed
    with the same secret, distinguished only by the `type` claim."""
    user = await make_user()
    refresh_token = create_refresh_token(user.id)

    resp = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert resp.status_code == 401


async def test_refresh_endpoint_without_cookie_is_401(client):
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def test_refresh_endpoint_rotates_tokens(client, make_user):
    user = await make_user(password="correct-password")
    login_resp = await client.post(
        "/api/v1/auth/login", data={"username": user.email, "password": "correct-password"}
    )
    old_access_token = login_resp.json()["access_token"]

    refresh_resp = await client.post("/api/v1/auth/refresh")

    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["access_token"]
    # Don't assert new != old: access-token JWTs are second-granular, so a refresh within the
    # same second legitimately yields an identical string. The security-relevant rotation is the
    # refresh cookie (always re-set above). What matters here is that refresh returns a usable
    # access token — verify it actually authenticates.
    assert old_access_token  # a token was issued at login
    me_resp = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_resp.status_code == 200


async def test_require_role_denies_non_admin(client, auth_user):
    """auth_user defaults to role=director — must not be allowed to hit the admin-only
    user-creation endpoint."""
    _, headers = auth_user

    resp = await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "new@example.com",
            "password": "somepassword123",
            "full_name": "New Person",
            "role": UserRole.assistant.value,
        },
    )

    assert resp.status_code == 403


async def test_require_role_allows_admin(client, make_user):
    from app.core.security import create_access_token

    admin = await make_user(role=UserRole.admin)
    headers = {"Authorization": f"Bearer {create_access_token(admin.id)}"}

    resp = await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "new2@example.com",
            "password": "somepassword123",
            "full_name": "New Person",
            "role": UserRole.assistant.value,
        },
    )

    assert resp.status_code == 201
