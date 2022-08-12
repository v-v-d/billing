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
    auth: aiohttp.BasicAuth = aiohttp.BasicAuth(
        settings.YOOKASSA_INTEGRATION.AUTH_USER,
        settings.YOOKASSA_INTEGRATION.AUTH_PASSWORD,
    ),

    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport

    async def _request(self, *args, **kwargs) -> Any:
        return await self.request(*args, **kwargs, auth=self.auth)

    async def pay(self, *args, **kwargs) -> None:
        await self._request(*args, **kwargs, auth=self.auth)


yookassa_client = YookassaHttpClient(AiohttpTransport())
