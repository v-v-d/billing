from logging import getLogger

import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.settings import settings

logger = getLogger(__name__)


def init_sentry(app: FastAPI) -> None:
    if not settings.SENTRY.ENABLED:
        return

    try:
        sentry_sdk.init(
            dsn=settings.SENTRY.DSN,
            debug=settings.SENTRY.DEBUG,
            sample_rate=settings.SENTRY.SAMPLE_RATE,
            environment=settings.SENTRY.ENVIRONMENT,
        )
        SentryAsgiMiddleware(app)
    except Exception as err:
        # Do not fall if sentry is not available
        logger.exception(err)
