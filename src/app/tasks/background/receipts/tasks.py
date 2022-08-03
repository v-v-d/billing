from typing import Any

from app.apm import apm_transaction


class BaseTaskError(Exception):
    """Base receipts background task error."""


@apm_transaction(
    name="Make receipt",
    transaction_type="background",
)
async def make_receipt(ctx: dict[str, Any]) -> None:
    pass
