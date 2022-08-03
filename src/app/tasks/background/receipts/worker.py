from typing import Any

from arq.connections import RedisSettings

from app.integrations.auth import AuthHttpClient
from app.redis import redis_settings
from app.settings import settings
from app.tasks.background.receipts import tasks
from app.transports import AiohttpTransport


async def startup(ctx: dict[str, Any]) -> None:
    auth_client = AuthHttpClient(AiohttpTransport())
    await auth_client.http_transport.startup()
    ctx["auth_client"] = auth_client


async def shutdown(ctx: dict[str, Any]) -> None:
    auth_client: AuthHttpClient = ctx["auth_client"]
    await auth_client.http_transport.shutdown()


class WorkerSettings:
    redis_settings: RedisSettings = redis_settings
    on_startup = startup
    on_shutdown = shutdown
    functions = [tasks.make_receipt]
    max_tries = settings.BACKGROUND.RECEIPT.MAX_TRIES
