from furl import furl
from pydantic import AnyHttpUrl, ValidationError

from app.integrations.async_api.exceptions import AsyncAPIHttpClientError
from app.integrations.async_api.schemas import FilmSchema
from app.integrations.base import AbstractHttpClient
from app.settings import settings
from app.transports import AbstractHttpTransport, AiohttpTransport


class AsyncAPIHttpClient(AbstractHttpClient):
    base_url: AnyHttpUrl = settings.ASYNC_API_INTEGRATION.BASE_URL
    client_exc: Exception = AsyncAPIHttpClientError

    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport

    async def get_film_details(self, film_id: str) -> FilmSchema:
        url = furl(self.base_url).add(path="/api/v1/films").add(path=film_id)

        response = await self.request(
            method="GET",
            url=url.url,
            timeout=settings.ASYNC_API_INTEGRATION.TIMEOUT_SEC,
        )

        try:
            return FilmSchema(**response)
        except ValidationError as err:
            raise self.client_exc(err) from err


async_api_client = AsyncAPIHttpClient(AiohttpTransport())
