import sqlalchemy as sa
from fastapi import APIRouter, Depends
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin.v1.schemas import TransactionSchema
from app.api.dependencies.database import get_db
from app.models import Transaction

router = APIRouter()


@router.get(
    "",
    response_model=LimitOffsetPage[TransactionSchema],
    description="Retrieve transactions",
)
async def get_transactions(db_session: AsyncSession = Depends(get_db)):
    return await paginate(db_session, sa.select(Transaction))
