import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.dependencies.database import get_db
from app.api.public.v1.schemas import PaymentNotificationSchema
from app.integrations.yookassa import (
    yookassa_client,
    YookassaHttpClientError,
    StatusEnum,
)
from app.models import Transaction, ObjectDoesNotExistError

router = APIRouter()
logger = logging.getLogger("notification")


@router.post("/yookassa/on-after-payment", description="Callback from yookassa")
async def on_after_payment(
    payment_data: PaymentNotificationSchema, db_session: AsyncSession = Depends(get_db)
):
    try:
        transaction_data = await yookassa_client.get_transaction(payment_data.object.id)
    except YookassaHttpClientError:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Yookassa unavailable.",
        )

    try:
        transaction = await Transaction.get(db_session, ext_id=payment_data.object.id)
    except ObjectDoesNotExistError:
        logger.exception(
            "Unknown transaction `id` received: %s", payment_data.object.id
        )
        return

    transaction.status = Transaction.StatusEnum(transaction_data.status.upper())

    if transaction_data.status == StatusEnum.SUCCEEDED:
        transaction.user_film.is_active = True
