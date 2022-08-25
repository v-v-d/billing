import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import UUID4
from sqlalchemy.orm import selectinload

from app.models import Transaction, ObjectDoesNotExistError
from app.api.dependencies.database import get_db
from app.api.admin.v1.schemas import TransactionOutput
from app.security import TokenData
from app.api.dependencies.auth import decode_jwt

router = APIRouter()


@router.get(
    "/",
    response_model=LimitOffsetPage[TransactionOutput],
    description="Retrieve user transactions",
)
async def get_users_transactions(
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt),
):
    user_id = jwt_payload.user_id
    return await paginate(
        db_session,
        sa.select(Transaction)
        .where(Transaction.user_id == user_id)
        .options(selectinload(Transaction.receipts))
        .options(selectinload(Transaction.user_film)),
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionOutput,
    description="Retrieve transaction",
)
async def get_transaction_by_id(
    transaction_id: UUID4,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt),
):
    user_id = jwt_payload.user_id

    try:
        template = await Transaction.get(db_session, id=transaction_id, user_id=user_id)
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return TransactionOutput.from_orm(template)
