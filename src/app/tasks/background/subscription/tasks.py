from typing import Any

from app.apm import apm_transaction


class BaseTaskError(Exception):
    """Base subscription background task error."""


@apm_transaction(
    name="Grant subscription",
    transaction_type="background",
)
async def grant_subscription(ctx: dict[str, Any]) -> None:
    pass
