import logging

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.dependencies.database import get_db
from app.api.public.v1.schemas import PaymentNotificationSchema
from app.integrations.yookassa import yookassa_client, YookassaHttpClientError
from app.models import Transaction

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

    if transaction_data.status == "succeeded":

        stmt = (
            sa.select(Transaction)
            .where(Transaction.ext_id == transaction_id)
            .options(selectinload(Transaction.user_film))
        )
        result = await db_session.execute(stmt)
        transaction = result.scalar()
        if not transaction:
            logger.exception("Unknown transaction `id` received: %s", transaction_id)
            return

        transaction.user_film.is_active = True
        transaction.status = Transaction.StatusEnum(transaction_data.status)
