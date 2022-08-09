from logging import config

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from fastapi_pagination import add_pagination

from app.api import init_api
from app.apm import init_apm
from app.integrations.auth import auth_client
from app.integrations.yookassa import yookassa_client
from app.sentry import init_sentry
from app.settings import settings
from app.settings.logging import LOGGING

config.dictConfig(LOGGING)

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    default_response_class=ORJSONResponse,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.SECURITY.ALLOWED_HOSTS)


@app.on_event("startup")
async def startup():
    await auth_client.startup()
    await yookassa_client.startup()


@app.on_event("shutdown")
async def shutdown():
    await auth_client.shutdown()
    await yookassa_client.shutdown()


init_api(app)
init_apm(app)
init_sentry(app)
add_pagination(app)
