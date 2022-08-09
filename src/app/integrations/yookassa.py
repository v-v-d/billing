from pydantic import AnyHttpUrl

from app.integrations.base import AbstractHttpClient
from app.settings import settings
from app.transports import AbstractHttpTransport, AiohttpTransport


class YookassaHttpClientError(Exception):
    pass


class YookassaHttpClient(AbstractHttpClient):
    base_url: AnyHttpUrl = settings.YOOKASSA_INTEGRATION.BASE_URL
    client_exc: Exception = YookassaHttpClientError

    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport


yookassa_client = YookassaHttpClient(AiohttpTransport())
