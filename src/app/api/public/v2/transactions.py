from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import SignatureValidator
from app.api.dependencies.database import get_db
from app.api.errors import TRANSACTION_NOT_FOUND
from app.api.public.v2.schemas import TransactionSchema
from app.api.schemas import ErrorSchema
from app.models import Transaction, ObjectDoesNotExistError
from app.settings import settings

router = APIRouter()


@router.get(
    "/{transaction_id}",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
    },
    response_model=TransactionSchema,
    description="Retrieve transaction",
    dependencies=[
        Depends(
            SignatureValidator(
                settings.YOOKASSA_INTEGRATION.SECRET_KEY,
                settings.YOOKASSA_INTEGRATION.SIGNATURE_EXPIRATION_HOURS,
            )
        ),
    ],
)
async def retrieve(
    transaction_id: UUID4,
    db_session: AsyncSession = Depends(get_db),
):
    try:
        transaction = await Transaction.get(db_session, id=transaction_id)
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=TRANSACTION_NOT_FOUND
        )

    return TransactionSchema.from_orm(transaction)
