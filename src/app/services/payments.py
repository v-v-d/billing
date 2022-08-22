from decimal import Decimal, ROUND_HALF_UP
from logging import getLogger

from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.async_api import async_api_client, AsyncAPIHttpClientError
from app.integrations.yookassa import yookassa_client, YookassaHttpClientError
from app.models import Transaction, Receipt, ReceiptItem, UserFilm

logger = getLogger(__name__)


class BasePaymentsServiceError(Exception):
    pass


class AlreadyPurchasedError(BasePaymentsServiceError):
    pass


class AsyncAPIUnavailableError(BasePaymentsServiceError):
    pass


class YookassaUnavailableError(BasePaymentsServiceError):
    pass


class PaymentsService:
    async def purchase_film(
        self,
        db_session: AsyncSession,
        user_id: str,
        film_id: str,
        payment_type: Transaction.PaymentType,
        idempotence_key: UUID4,
    ) -> str:
        user_film, _ = await UserFilm.get_or_create(
            db_session, user_id=user_id, film_id=film_id,
        )

        if user_film.is_active:
            raise AlreadyPurchasedError

        try:
            film = await async_api_client.get_film_details(film_id)
        except AsyncAPIHttpClientError:
            raise AsyncAPIUnavailableError

        if film.price <= 0:
            raise AlreadyPurchasedError

        transaction = await Transaction.create(
            db_session,
            user_id=user_id,
            amount=film.price,
            type=Transaction.TypeEnum.PAYMENT,
            payment_type=payment_type,
        )
        transaction_id = transaction.id  # prevent sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called

        receipt = await Receipt.create(db_session, transaction_id=transaction.id)
        await ReceiptItem.create(
            db_session,
            receipt_id=receipt.id,
            description=film.title,
            quantity=1,
            amount=film.price,
            type=ReceiptItem.TypeEnum.FILM,
        )

        valid_price = (Decimal(film.price) / 100).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )

        try:
            yookassa_data = await yookassa_client.pay(
                valid_price, transaction_id, idempotence_key
            )
        except YookassaHttpClientError:
            raise YookassaUnavailableError

        transaction.ext_id = yookassa_data.id
        user_film.transaction = transaction

        return yookassa_data.confirmation.confirmation_url


payments_service = PaymentsService()
