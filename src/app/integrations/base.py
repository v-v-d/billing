from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import AnyHttpUrl

from app.transports import AbstractHttpTransport, BaseTransportError


class BaseClientError(Exception):
    pass


class AbstractHttpClient(ABC):  # pragma: no cover
    @abstractmethod
    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport

    @abstractmethod
    def base_url(self) -> AnyHttpUrl:
        pass

    @abstractmethod
    def client_exc(self) -> Type[Exception]:
        pass

    async def startup(self) -> None:
        await self.http_transport.startup()

    async def shutdown(self) -> None:
        await self.http_transport.shutdown()

    async def request(self, *args, **kwargs) -> Any:
        try:
            return await self.http_transport.request(*args, **kwargs)
        except BaseTransportError as err:
            raise self.client_exc(err.message) from err
