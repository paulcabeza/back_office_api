"""Shared fixtures for all tests.

Env vars are set BEFORE any app import so that Settings() doesn't blow up in CI.
"""

import os
import uuid
from unittest.mock import AsyncMock, MagicMock

# ── Env vars (must come before app imports) ──────────────────────────────
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://fake:fake@localhost/fake")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://fake:fake@localhost/fake")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.deps import get_current_user
from app.db.session import get_db
from app.main import app as fastapi_app


# ── Helpers ──────────────────────────────────────────────────────────────

def make_fake_user(*, is_superadmin: bool = False, permissions: set[str] | None = None):
    """Return a MagicMock that quacks like a User model instance."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.is_superadmin = is_superadmin

    _perms = permissions or set()
    user.has_permission = lambda codename: is_superadmin or codename in _perms
    return user


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture()
def app():
    """Yield the FastAPI app and clean up dependency overrides after test."""
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
async def client(app):
    """Async httpx client wired to the FastAPI app (no real server needed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def override_auth(app):
    """Factory fixture: override get_current_user with a fake user.

    Usage:
        override_auth(make_fake_user(is_superadmin=True))
    """
    def _override(fake_user):
        app.dependency_overrides[get_current_user] = lambda: fake_user
    return _override


@pytest.fixture()
def override_db(app):
    """Factory fixture: override get_db with an AsyncMock session.

    Usage:
        mock_db = AsyncMock()
        override_db(mock_db)
    """
    def _override(mock_session):
        async def _fake_get_db():
            yield mock_session
        app.dependency_overrides[get_db] = _fake_get_db
    return _override
