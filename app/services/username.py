"""Shared username generation logic."""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


def _normalize(text: str) -> str:
    """Remove accents and convert to ASCII lowercase."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", ascii_only.lower())


async def generate_username(
    db: AsyncSession, first_name: str, last_name: str
) -> str:
    """Auto-generate a unique username from name parts.

    Rules:
      1. First letter of first name + first last name -> e.g. "rcabrera"
      2. If taken, append first letter of second last name -> "rcabrerar"
      3. If still taken, append incremental number -> "rcabrera1", "rcabrera2"
    """
    names = first_name.strip().split()
    surnames = last_name.strip().split()

    first_initial = _normalize(names[0])[0] if names else "x"
    primary_surname = _normalize(surnames[0]) if surnames else "user"
    second_surname_initial = _normalize(surnames[1])[0] if len(surnames) > 1 else ""

    # Attempt 1: first initial + primary surname
    candidate = f"{first_initial}{primary_surname}"
    result = await db.execute(select(User).where(User.username == candidate))
    if result.scalar_one_or_none() is None:
        return candidate

    # Attempt 2: append second surname initial
    if second_surname_initial:
        candidate2 = f"{candidate}{second_surname_initial}"
        result = await db.execute(select(User).where(User.username == candidate2))
        if result.scalar_one_or_none() is None:
            return candidate2

    # Attempt 3: numeric suffix
    counter = 1
    while True:
        candidate_n = f"{candidate}{counter}"
        result = await db.execute(select(User).where(User.username == candidate_n))
        if result.scalar_one_or_none() is None:
            return candidate_n
        counter += 1
