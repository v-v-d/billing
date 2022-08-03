from logging import config

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from fastapi_pagination import add_pagination

from app.amqp import publisher
from app.api import init_api
from app.apm import init_apm
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
    await publisher.connect()


@app.on_event("shutdown")
async def shutdown():
    await publisher.disconnect()


init_api(app)
init_apm(app)
init_sentry(app)
add_pagination(app)
