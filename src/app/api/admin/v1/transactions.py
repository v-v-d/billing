from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.async_sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, ObjectDoesNotExistError,
from app.api.dependencies.database import get_db
from schemas import TransactionOutput

router = APIRouter()


@router.get("/{transaction_id}", response_model=TransactionOutput, description="Retrive transaction")
async def get_transaction_by_id(transaction_id: UUID4, db_session: AsyncSession = Depends(get_db)):
    try:
        transaction = await Transaction.get_by_id(db_session, transaction_id)
    except ObjectDoesNotExistError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Transaction not found")
    return TransactionOutput.from_orm(transaction)




