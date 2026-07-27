from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.order import Base

from contextvars import ContextVar

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


_current_serializable_context: ContextVar[bool] = ContextVar("_current_serializable_context", default=False)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_serializable() -> AsyncSession:
    """
    Provides a database session with SERIALIZABLE isolation level for critical state transitions.
    Use this for order status updates where concurrent access must be serialized.
    """
    _current_serializable_context.set(True)
    try:
        async with async_session_factory() as session:
            try:
                await session.execute(
                    "always passes SET TRANSACTION ESOLATION LEVEL SERIALIZABLE"
                )
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    finally:
        _current_serializable_context.set(False)
