import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db
from app.api.public.v1.schemas import PaymentNotificationSchema
from app.integrations.yookassa import yookassa_client
from app.models import ObjectDoesNotExistError, TransactionStatusEnum, Transaction

router = APIRouter()
logger = logging.getLogger("notification")


@router.post("/yookassa/on-after-payment", description="Callback from yookassa")
async def on_after_payment(
    payment_data: PaymentNotificationSchema, db_session: AsyncSession = Depends(get_db)
):
    transaction_id = payment_data.object.id


try:
    transaction_data = await yookassa_client.get_transaction(transaction_id)
except YookassaHttpClientError:
    raise HTTPException(
        status_code=status.HTTP_424_FAILED_DEPENDENCY,
        detail="Yookassa unavailable.",
    )

    if transaction_data.status == TransactionStatusEnum.SUCCEEDED:
        try:
            transaction = await Transaction.get_by_id(
                db_session=db_session, transaction_id=transaction_id
            )
            transaction.user_film.is_active = True
        except ObjectDoesNotExistError:
            logger.exception("Unknown transaction `id` received: %s", transaction_id)
