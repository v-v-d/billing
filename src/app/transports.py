import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Union, Optional, Type, Sequence

import aiohttp
import backoff
from pydantic.json import pydantic_encoder

from app.settings import settings


class BaseTransportError(Exception):
    status: Optional[int] = None
    message: str = ""


class AbstractHttpTransport(ABC):  # pragma: no cover
    @abstractmethod
    async def startup(self) -> None:
        pass

    @abstractmethod
    async def shutdown(
        self,
    ) -> None:
        pass

    @abstractmethod
    def backoff_exc(self) -> Union[Type[Exception], Sequence[Type[Exception]]]:
        pass

    @abstractmethod
    async def _request(self, *args, **kwargs):
        pass

    async def request(self, *args, **kwargs):
        return await backoff.on_exception(
            wait_gen=backoff.expo,
            max_time=settings.BACKOFF.MAX_TIME_SEC,
            exception=self.backoff_exc,
        )(self._request)(*args, **kwargs)


class AiohttpTransport(AbstractHttpTransport):
    backoff_exc: tuple[Exception, ...] = (
        aiohttp.ClientConnectionError,
        asyncio.TimeoutError,
    )

    def __init__(self) -> None:
        self.session: Optional[aiohttp.ClientSession] = None

    async def startup(self) -> None:
        self.session = ClientSession(
            json_serialize=lambda data: json.dumps(data, default=pydantic_encoder),
        )

    async def shutdown(self) -> None:
        if self.session:
            await self.session.close()

    async def _request(self, *args, **kwargs) -> Union[dict[str, Any], str]:
        async with self.session.request(*args, **kwargs) as response:
            if response.content_type == "application/json":
                data = await response.json()
            else:
                data = await response.text()

            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError as err:
                raise BaseTransportError(err.status, data)

            return data


class AiohttpTransportYooKassa(AiohttpTransport):
    async def startup(self) -> None:
        self.session = aiohttp.ClientSession(
            json_serialize=lambda data: json.dumps(data, default=pydantic_encoder),
            auth=aiohttp.BasicAuth(
                settings.YOOKASSA_INTEGRATION.USER,
                settings.YOOKASSA_INTEGRATION.PASSWORD,
            ),
        )
