from logging import getLogger

logger = getLogger(__name__)


class BaseTransactionsServiceError(Exception):
    """Base transactions service error."""


class TransactionsService:
    pass


def get_transactions_service() -> TransactionsService:
    return TransactionsService()
