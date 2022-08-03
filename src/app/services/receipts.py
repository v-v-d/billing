from logging import getLogger

logger = getLogger(__name__)


class BaseReceiptsServiceError(Exception):
    """Base receipts service error."""


class ReceiptsService:
    pass


def get_receipts_service() -> ReceiptsService:
    return ReceiptsService()
