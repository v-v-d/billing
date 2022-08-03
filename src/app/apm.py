from functools import wraps
from typing import Optional, Callable

import elasticapm
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM
from fastapi import FastAPI

from app.settings import settings


def init_apm(app: FastAPI):
    if not settings.APM.ENABLED:
        return

    apm = make_apm_client(
        enabled=settings.APM.ENABLED,
        server_url=settings.APM.SERVER_URL,
        service_name=settings.APM.SERVICE_NAME,
        environment=settings.APM.ENVIRONMENT,
    )
    app.add_middleware(ElasticAPM, client=apm)


def apm_transaction(
    name: str,
    transaction_type: str,
    labels_builder: Optional[Callable] = None,
) -> Callable:
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            if not settings.APM.ENABLED:
                return await f(*args, **kwargs)

            apm_client = elasticapm.get_client()

            if not apm_client:
                apm_client = make_apm_client(config=settings.APM.dict())
                elasticapm.instrument()

            apm_client.begin_transaction(transaction_type=transaction_type)

            if labels_builder:
                labels = labels_builder(f, *args, **kwargs)
                elasticapm.label(**labels)

            try:
                result = await f(*args, **kwargs)
            except Exception as err:
                apm_client.capture_exception()
                apm_client.end_transaction(name=name, result="error")
                raise err

            apm_client.end_transaction(name=name, result="success")

            return result

        return wrapper

    return decorator
