import base64
import hashlib
import hmac
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Type
from urllib.parse import quote_plus

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


class SignatureMixin(ABC):
    @abstractmethod
    def secret_key(self) -> str:
        pass

    def make_signature(self, urlencoded: bool = True) -> tuple[str, str]:
        date = datetime.utcnow().isoformat(timespec="milliseconds")
        message = bytes(date, "utf-8")
        secret = bytes(self.secret_key, "utf-8")

        signature = base64.b64encode(
            hmac.new(secret, message, digestmod=hashlib.sha256).digest()
        ).decode()

        if urlencoded:
            signature, date = quote_plus(signature), quote_plus(date)

        return signature, date
