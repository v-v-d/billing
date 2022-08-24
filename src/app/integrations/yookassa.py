import json
from typing import Any

import aiohttp
from furl import furl
from pydantic import AnyHttpUrl, ValidationError, UUID4

from app.api.public.v1.schemas import PaymentObjectSchema
from app.integrations.base import AbstractHttpClient
from app.settings import settings
from app.transports import AbstractHttpTransport, AiohttpTransport


class YookassaHttpClientError(Exception):
    pass


class YookassaHttpClient(AbstractHttpClient):
    base_url: AnyHttpUrl = settings.YOOKASSA_INTEGRATION.BASE_URL
    client_exc: Exception = YookassaHttpClientError
    auth: aiohttp.BasicAuth = aiohttp.BasicAuth(
        settings.YOOKASSA_INTEGRATION.AUTH_USER,
        settings.YOOKASSA_INTEGRATION.AUTH_PASSWORD,
    )

    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport

    async def _request(self, *args, **kwargs) -> Any:
        return await self.request(*args, **kwargs, auth=self.auth)

    async def pay(self, *args, **kwargs) -> None:
        await self._request(*args, **kwargs, auth=self.auth)

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


yookassa_client = YookassaHttpClient(AiohttpTransport())
