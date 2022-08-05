from typing import Optional

from fastapi import Header

from app.context import update_context


async def store_request_meta_to_ctx(
    x_request_id: Optional[str] = Header(default=None),
) -> None:
    await update_context(x_request_id=x_request_id)
