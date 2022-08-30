from decimal import Decimal, ROUND_HALF_UP
from logging import getLogger

from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.async_api.client import async_api_client, AsyncAPIHttpClientError
from app.integrations.yookassa.client import yookassa_client, YookassaHttpClientError
from app.integrations.yookassa.schemas import StatusEnum
from app.models import Transaction, Receipt, ReceiptItem, UserFilm
from app.services.payments.exceptions import (
    AlreadyPurchasedError,
    AsyncAPIUnavailableError,
    YookassaUnavailableError,
    YookassaRefundError,
    PermissionDeniedError,
    IncorrectTransactionStatusError,
    NotAvalableForRefundError,
    AlreadyWatchedError,
)

logger = getLogger(__name__)


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
            db_session,
            user_id=user_id,
            film_id=film_id,
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

        receipt = await Receipt.create(db_session, transaction_id=transaction.id)
        receipt_item = await ReceiptItem.create(
            db_session,
            receipt_id=receipt.id,
            description=film.title,
            quantity=1,
            amount=film.price,
            type=ReceiptItem.TypeEnum.FILM,
        )

        await db_session.flush()
        receipt.transaction_id = transaction.id
        receipt_item.receipt_id = receipt.id

        valid_price = (Decimal(film.price) / 100).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )

        try:
            yookassa_data = await yookassa_client.pay(
                valid_price, transaction.id, idempotence_key
            )
        except YookassaHttpClientError:
            raise YookassaUnavailableError

        transaction.ext_id = yookassa_data.id
        user_film.transaction = transaction

        return yookassa_data.confirmation.confirmation_url

    async def refund_film(
        self,
        db_session: AsyncSession,
        transaction_id: str,
        user_id: str,
        idempotence_key: UUID4,
    ) -> Transaction:
        payment_transaction = await Transaction.get(db_session, id=transaction_id)

        self.validate_transaction_for_refund(payment_transaction, user_id)

        refund_transaction = await Transaction.create(
            db_session,
            user_id=user_id,
            amount=payment_transaction.amount,
            type=Transaction.TypeEnum.REFUND,
            payment_type=payment_transaction.payment_type,
        )
        refund_receipt = await Receipt.create(
            db_session, transaction_id=refund_transaction.id
        )

        refund_receipt_items = [
            await ReceiptItem.create(
                db_session,
                receipt_id=refund_receipt.id,
                description=payment_receipt_item.description,
                quantity=payment_receipt_item.quantity,
                amount=payment_receipt_item.amount,
                type=payment_receipt_item.type,
            )
            for payment_receipt_item in payment_transaction.receipt.items
        ]

        refund_receipt.items = refund_receipt_items
        refund_transaction.receipt = refund_receipt
        refund_transaction.user_film = payment_transaction.user_film

        await db_session.flush()

        refund_receipt.transaction_id = refund_transaction.id

        for refund_receipt_item in refund_receipt_items:
            refund_receipt_item.receipt_id = refund_receipt.id

        valid_amount = (Decimal(refund_transaction.amount) / 100).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )

        try:
            transaction_data = await yookassa_client.refund(
                valid_amount,
                payment_transaction.ext_id,
                idempotence_key,
            )
        except YookassaHttpClientError:
            raise YookassaUnavailableError

        if transaction_data.status == StatusEnum.CANCELED:
            raise YookassaRefundError

        refund_transaction.status = Transaction.StatusEnum(
            transaction_data.status.upper()
        )
        payment_transaction.user_film.is_active = False

        return refund_transaction

    @staticmethod
    def validate_transaction_for_refund(transaction: Transaction, user_id: str) -> None:
        if str(transaction.user_id) != user_id:
            raise PermissionDeniedError

        if transaction.status != Transaction.StatusEnum.SUCCEEDED:
            raise IncorrectTransactionStatusError

        if (
            not transaction.ext_id
            or not transaction.user_film
            or not transaction.user_film.is_active
        ):
            raise NotAvalableForRefundError

        if transaction.user_film.watched:
            raise AlreadyWatchedError


payments_service = PaymentsService()
