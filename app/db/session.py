import ssl as _ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _clean_url(url: str) -> str:
    """Strip query params from DATABASE_URL — asyncpg doesn't accept sslmode, channel_binding, etc."""
    return url.split("?")[0]


# Neon requires SSL; asyncpg needs it via connect_args, not query string
_ssl_ctx = _ssl.create_default_context()

engine = create_async_engine(
    _clean_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    connect_args={"ssl": _ssl_ctx},
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
