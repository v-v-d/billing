from fastapi import APIRouter, Depends
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.orm import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction
from app.api.dependencies.database import get_db
from app.api.admin.v1.schemas import TransactionOutput
from app.security import TokenData, decode_jwt_token

router = APIRouter()


@router.get(
    "/",
    response_model=LimitOffsetPage[TransactionOutput],
    description="Retrieve users transaction",
)
async def get_users_transactions(
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt_token),
):
    user_id = jwt_payload.user_id
    transactions = await Transaction.get(db_session, user_id=user_id)
    return paginate(TransactionOutput.from_orm(transactions))
