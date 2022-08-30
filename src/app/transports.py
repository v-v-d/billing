import asyncio
import json
from abc import ABC, abstractmethod
from logging import getLogger
from types import SimpleNamespace
from typing import Any, Union, Optional, Type, Sequence

import aiohttp
import backoff
from pydantic.json import pydantic_encoder

from app.settings import settings

logger = getLogger(__name__)


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
        self._auth: Optional[aiohttp.BasicAuth] = None

    @property
    def auth(self) -> Optional[aiohttp.BasicAuth]:
        return self._auth

    @auth.setter
    def auth(self, value: tuple[str, str]) -> None:
        self._auth = aiohttp.BasicAuth(*value)

    async def startup(self) -> None:
        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(self.on_request_start)
        trace_config.on_request_end.append(self.on_request_end)
        trace_config.on_request_exception.append(self.on_request_exception)

        self.session = aiohttp.ClientSession(
            json_serialize=lambda data: json.dumps(data, default=pydantic_encoder),
            trace_configs=[trace_config],
        )

    async def shutdown(self) -> None:
        if self.session:
            await self.session.close()

    async def _request(self, *args, **kwargs) -> Union[dict[str, Any], str]:
        async with self.session.request(*args, **kwargs, auth=self.auth) as response:
            if response.content_type == "application/json":
                data = await response.json()
            else:
                data = await response.text()

            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError as err:
                raise BaseTransportError(err.status, data)

            return data

    async def on_request_start(
        self,
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestStartParams,
    ) -> None:
        logger.info("Server make request %s", params)

    async def on_request_end(
        self,
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestEndParams,
    ) -> None:
        logger.info("Server got response %s", params)

    async def on_request_exception(
        self,
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestExceptionParams,
    ) -> None:
        logger.error("Server got request exception %s", params)
