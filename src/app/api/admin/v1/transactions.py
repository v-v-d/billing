from fastapi import APIRouter, Depends
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.orm import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction
from app.api.dependencies.database import get_db
from app.api.admin.v1.schemas import TransactionOutput

router = APIRouter()


@router.get(
    "/",
    response_model=LimitOffsetPage[TransactionOutput],
    description="Retrieve transaction",
)
async def get_users_transactions(db_session: AsyncSession = Depends(get_db)):
    transactions = await Transaction.get(db_session)
    return paginate(TransactionOutput.from_orm(transactions))
