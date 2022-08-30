from decimal import Decimal
from typing import Any

from furl import furl
from pydantic import AnyHttpUrl, UUID4, ValidationError

from app.api.public.v1.schemas import PaymentObjectSchema
from app.integrations.base import AbstractHttpClient, SignatureMixin
from app.integrations.yookassa.exceptions import YookassaHttpClientError
from app.integrations.yookassa.schemas import (
    YookassaPaymentResponseSchema,
    YookassaRefundResponseSchema,
)
from app.settings import settings
from app.transports import AbstractHttpTransport, AiohttpTransport


class YookassaHttpClient(AbstractHttpClient, SignatureMixin):
    base_url: AnyHttpUrl = settings.YOOKASSA_INTEGRATION.BASE_URL
    client_exc: Exception = YookassaHttpClientError
    secret_key = settings.YOOKASSA_INTEGRATION.SECRET_KEY

    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport
        self.http_transport.auth = (
            settings.YOOKASSA_INTEGRATION.AUTH_USER,
            settings.YOOKASSA_INTEGRATION.AUTH_PASSWORD,
        )

    async def _request(self, *args, **kwargs) -> Any:
        return await self.request(*args, **kwargs)

    async def pay(
        self,
        price: Decimal,
        transaction_id: UUID4,
        idempotence_key: UUID4,
    ) -> YookassaPaymentResponseSchema:
        signature, date = self.make_signature()

        return_url = settings.YOOKASSA_INTEGRATION.RETURN_URL_PATTERN.format(
            transaction_id, signature, date
        )
        data = {
            "capture": True,
            "amount": {
                "value": str(price),
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url,
            },
        }
        headers = {"Idempotence-Key": str(idempotence_key)}
        url = furl(self.base_url).add(path="/v3/payments")

        response = await self._request(
            method="POST", url=url.url, json=data, headers=headers
        )

        try:
            return YookassaPaymentResponseSchema(**response)
        except ValidationError as err:
            raise self.client_exc(str(err)) from err

    async def get_transaction(self, transaction_id: UUID4) -> PaymentObjectSchema:
        """
        Gets transaction info from  yookassa by GET request to URL:
        https://api.yookassa.ru/v3/payments/{payment_id}
        """
        url = furl(self.base_url).add(path="/v3/payments").add(path=str(transaction_id))
        result = await self._request(method="GET", url=url.url)

        try:
            return PaymentObjectSchema(**result)
        except ValidationError as err:
            raise self.client_exc(str(err)) from err

    async def refund(
        self,
        amount: Decimal,
        payment_transaction_ext_id: UUID4,
        idempotence_key: UUID4,
    ) -> YookassaRefundResponseSchema:
        data = {
            "amount": {
                "value": str(amount),
                "currency": "RUB",
            },
            "payment_id": payment_transaction_ext_id,
        }
        headers = {"Idempotence-Key": str(idempotence_key)}
        url = furl(self.base_url).add(path="/v3/refunds")

        response = await self._request(
            method="POST", url=url.url, json=data, headers=headers
        )

        try:
            return YookassaRefundResponseSchema(**response)
        except ValidationError as err:
            raise self.client_exc(str(err)) from err


yookassa_client = YookassaHttpClient(AiohttpTransport())
