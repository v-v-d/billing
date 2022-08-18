from furl import furl
from pydantic import AnyHttpUrl, ValidationError, BaseModel, UUID4

from app.integrations.base import AbstractHttpClient
from app.settings import settings
from app.transports import AbstractHttpTransport, AiohttpTransport
from typing import Optional


class AuthHttpClientError(Exception):
    pass


class UserSchema(BaseModel):
    id: UUID4
    email: Optional[str]
    phone: Optional[str]


class AuthHttpClient(AbstractHttpClient):
    base_url: AnyHttpUrl = settings.AUTH_INTEGRATION.BASE_URL
    client_exc: Exception = AuthHttpClientError

    def __init__(self, http_transport: AbstractHttpTransport) -> None:
        self.http_transport: AbstractHttpTransport = http_transport

    async def get_user_details(self, user_id: UUID4) -> UserSchema:
        url = (
            furl(self.base_url)
            .add(path="/api/internal/v1/users")
            .add(path=user_id)
            .add(path="info")
        )
        response = await self.request(
            method="GET", url=url.url, timeout=settings.AUTH_INTEGRATION.TIMEOUT_SEC
        )
        try:
            return UserSchema(**response)
        except ValidationError as err:
            raise self.client_exc(err) from err


auth_client = AuthHttpClient(AiohttpTransport())
