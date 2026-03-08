from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.config import DATABASE_URL

engine = None
_sessionmaker = None


def get_sessionmaker():
    global engine, _sessionmaker

    if _sessionmaker is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")

        engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
        _sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False, class_=AsyncSession
        )

    return _sessionmaker
