"""Username generation tests — mock db.execute to simulate collisions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.username import _normalize, generate_username


# ── _normalize tests ─────────────────────────────────────────────────────

def test_normalize_removes_accents():
    assert _normalize("José") == "jose"


def test_normalize_removes_special_chars():
    assert _normalize("O'Brien-Smith") == "obriensmith"


# ── generate_username tests ──────────────────────────────────────────────

def _mock_db(taken_usernames: set[str]) -> AsyncMock:
    """Build an AsyncMock db where execute().scalar_one_or_none() returns
    a truthy value for usernames in `taken_usernames`, None otherwise."""
    db = AsyncMock()

    def _execute_side_effect(stmt):
        # Extract the username being checked from the compiled WHERE clause
        result = MagicMock()
        # Get the bound parameter value from the statement
        username = stmt.whereclause.right.value
        result.scalar_one_or_none.return_value = (
            "taken" if username in taken_usernames else None
        )
        return result

    db.execute = AsyncMock(side_effect=_execute_side_effect)
    return db


async def test_basic_username():
    """'Roberto Cabrera' -> 'rcabrera'"""
    db = _mock_db(set())
    result = await generate_username(db, "Roberto", "Cabrera Lopez")
    assert result == "rcabrera"


async def test_collision_uses_second_surname():
    """If 'rcabrera' is taken, try 'rcabreral' (second surname initial)."""
    db = _mock_db({"rcabrera"})
    result = await generate_username(db, "Roberto", "Cabrera Lopez")
    assert result == "rcabreral"


async def test_double_collision_uses_numeric_suffix():
    """If both 'rcabrera' and 'rcabreral' are taken, fallback to 'rcabrera1'."""
    db = _mock_db({"rcabrera", "rcabreral"})
    result = await generate_username(db, "Roberto", "Cabrera Lopez")
    assert result == "rcabrera1"
