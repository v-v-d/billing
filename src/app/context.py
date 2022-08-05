import logging
from contextvars import ContextVar
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ContextSchema(BaseModel):
    x_request_id: Optional[str]


ctx: ContextVar[ContextSchema] = ContextVar("context", default=ContextSchema())


async def update_context(**kwargs) -> None:
    try:
        current_ctx = ctx.get()
        ctx.set(current_ctx.copy(update={**kwargs}))
    except Exception as err:
        logger.exception(err)
