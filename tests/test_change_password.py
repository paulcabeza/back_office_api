"""Tests for POST /api/v1/auth/change-password."""

from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import make_fake_user


# ── Tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_change_password_success(client, override_auth, override_db):
    """Successful password change returns 204 and updates the hash."""
    fake_user = make_fake_user(password_hash="old_hash", must_change_password=True)
    override_auth(fake_user)

    mock_db = AsyncMock()
    override_db(mock_db)

    with patch("app.api.v1.endpoints.auth.verify_password", return_value=True), \
         patch("app.api.v1.endpoints.auth.hash_password", return_value="new_hash"):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "OldPass123", "new_password": "NewPass123"},
        )

    assert resp.status_code == 204
    assert fake_user.password_hash == "new_hash"
    assert fake_user.must_change_password is False


@pytest.mark.asyncio
async def test_change_password_wrong_current(client, override_auth, override_db):
    """Wrong current password returns 400."""
    fake_user = make_fake_user(password_hash="old_hash")
    override_auth(fake_user)

    mock_db = AsyncMock()
    override_db(mock_db)

    with patch("app.api.v1.endpoints.auth.verify_password", return_value=False):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "WrongPass1", "new_password": "NewPass123"},
        )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Current password is incorrect"


@pytest.mark.asyncio
async def test_change_password_short_new_password(client, override_auth, override_db):
    """New password shorter than 8 chars returns 422."""
    fake_user = make_fake_user()
    override_auth(fake_user)

    mock_db = AsyncMock()
    override_db(mock_db)

    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "OldPass123", "new_password": "short"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_change_password_clears_flag(client, override_auth, override_db):
    """must_change_password flag is set to False after successful change."""
    fake_user = make_fake_user(must_change_password=True, password_hash="old_hash")
    override_auth(fake_user)

    mock_db = AsyncMock()
    override_db(mock_db)

    with patch("app.api.v1.endpoints.auth.verify_password", return_value=True), \
         patch("app.api.v1.endpoints.auth.hash_password", return_value="new_hash"):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "OldPass123", "new_password": "NewPass123"},
        )

    assert resp.status_code == 204
    assert fake_user.must_change_password is False
