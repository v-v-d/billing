import json
from typing import Any

import aiohttp
from pydantic import AnyHttpUrl

from app.integrations.base import AbstractHttpClient
from app.settings import settings
from app.transports import AbstractHttpTransport, AiohttpTransport


class YookassaHttpClientError(Exception):
    pass


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

    async def pay(self, *args, **kwargs) -> None:
        await self._request(*args, **kwargs, auth=self.auth)

    async def check_transaction(self, transaction_id: str) -> str:
        """
        Checks transaction status in yookassa by GET request on URL:
        https://api.yookassa.ru/v3/payments/{payment_id}
        """
        check_transaction_url = "{}/payments/{}".format(
            self.base_url,
            transaction_id
        )
        result = await self._request(method="GET",
                                     url=check_transaction_url,
                                     auth=self.auth)

        result_json = json.loads(result)
        return result_json.get("status", "")


yookassa_client = YookassaHttpClient(AiohttpTransport())
