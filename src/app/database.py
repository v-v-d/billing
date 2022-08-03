from contextlib import asynccontextmanager

from sqlalchemy import MetaData
from sqlalchemy.ext import asyncio as sa_asyncio
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import settings

engine = sa_asyncio.create_async_engine(
    settings.DB.DSN, pool_recycle=settings.DB.POOL_RECYCLE
)
Session = sessionmaker(bind=engine, class_=sa_asyncio.AsyncSession)
metadata = MetaData(schema=settings.DB.SCHEMA)
Base = declarative_base(metadata=metadata)


@asynccontextmanager
async def session_scope():
    """Provide a transactional scope around a series of operations."""

    async_session = Session()

    try:
        yield async_session
        await async_session.commit()
    except Exception:
        await async_session.rollback()
        raise
    finally:
        await async_session.close()
