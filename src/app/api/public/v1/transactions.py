import sqlalchemy as sa
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import UUID4

from app.models import Transaction, ObjectDoesNotExistError
from app.api.dependencies.database import get_db
from app.api.admin.v1.schemas import TransactionOutput
from app.security import TokenData, decode_jwt_token

router = APIRouter()


@router.get(
    "/",
    response_model=LimitOffsetPage[TransactionOutput],
    description="Retrieve user transactions",
)
async def get_users_transactions(
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt_token),
):
    user_id = jwt_payload.user_id
    return paginate(
        db_session, sa.select(Transaction).where(Transaction.user_id == user_id)
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionOutput,
    description="Retrieve transaction",
)
async def get_template_by_id(
    transaction_id: UUID4,
    db_session: AsyncSession = Depends(get_db),
):
    try:
        template = await Transaction.get(db_session, id=transaction_id)
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Transaction not found"
        )

    return TransactionOutput.from_orm(template)
