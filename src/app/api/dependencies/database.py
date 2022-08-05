from typing import AsyncIterator

from app.database import session_scope
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncIterator[AsyncSession]:
    async with session_scope() as session:
        yield session
