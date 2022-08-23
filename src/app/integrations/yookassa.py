from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import aiohttp
from pydantic import AnyHttpUrl, UUID4, BaseModel, ValidationError

from app.integrations.base import AbstractHttpClient
from app.settings import settings
from app.transports import AbstractHttpTransport, AiohttpTransport


class YookassaHttpClientError(Exception):
    pass


class StatusEnum(str, Enum):
    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class ResponseConfirmationSchema(BaseModel):
    confirmation_url: AnyHttpUrl


class YookassaPaymentResponseSchema(BaseModel):
    id: UUID
    status: StatusEnum
    confirmation: ResponseConfirmationSchema


class YookassaHttpClient(AbstractHttpClient):
    base_url: AnyHttpUrl = settings.YOOKASSA_INTEGRATION.BASE_URL
    client_exc: Exception = YookassaHttpClientError
    auth: aiohttp.BasicAuth = (
        aiohttp.BasicAuth(
            settings.YOOKASSA_INTEGRATION.AUTH_USER,
            settings.YOOKASSA_INTEGRATION.AUTH_PASSWORD,
        ),
    )

    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport

    async def _request(self, *args, **kwargs) -> Any:
        return await self.request(*args, **kwargs, auth=self.auth)

    async def pay(
        self,
        price: Decimal,
        transaction_id: UUID4,
        idempotence_key: UUID4,
    ) -> YookassaPaymentResponseSchema:
        return_url = settings.YOOKASSA_INTEGRATION.RETURN_URL_PATTERN.format(
            transaction_id
        )
        data = {
            "amount": {
                "value": str(price),
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url,
            },
        }
        headers = {"Idempotence-Key": idempotence_key}

        response = await self._request(method="POST", json=data, headers=headers)

        try:
            return YookassaPaymentResponseSchema(**response)
        except ValidationError as err:
            raise self.client_exc(str(err)) from err


yookassa_client = YookassaHttpClient(AiohttpTransport())
