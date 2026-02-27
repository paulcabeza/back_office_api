"""DELETE /api/v1/affiliates/{id} endpoint tests via httpx."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import make_fake_user


AFFILIATE_ID = uuid.uuid4()
URL = f"/api/v1/affiliates/{AFFILIATE_ID}"


def _mock_db_with_affiliate():
    """Mock db where the affiliate exists."""
    db = AsyncMock()
    affiliate = MagicMock()
    affiliate.tenant_id = uuid.uuid4()
    affiliate.affiliate_code = "SV-0001"
    affiliate.email = "affiliate@example.com"
    result = MagicMock()
    result.scalar_one_or_none.return_value = affiliate
    db.execute.return_value = result
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _mock_db_no_affiliate():
    """Mock db where the affiliate does not exist."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result
    return db


async def test_superadmin_can_delete(client, override_auth, override_db):
    """Superadmin with delete permission -> 204 No Content."""
    override_auth(make_fake_user(is_superadmin=True))
    override_db(_mock_db_with_affiliate())

    resp = await client.delete(URL)
    assert resp.status_code == 204


async def test_non_superadmin_gets_403(client, override_auth, override_db):
    """Regular user (even with affiliates:delete permission) -> 403."""
    override_auth(make_fake_user(permissions={"affiliates:delete"}))
    override_db(_mock_db_no_affiliate())

    resp = await client.delete(URL)
    assert resp.status_code == 403


async def test_affiliate_not_found_returns_404(client, override_auth, override_db):
    """Superadmin tries to delete non-existent affiliate -> 404."""
    override_auth(make_fake_user(is_superadmin=True))
    override_db(_mock_db_no_affiliate())

    resp = await client.delete(URL)
    assert resp.status_code == 404
