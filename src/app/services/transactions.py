import sqlalchemy as sa
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.async_sqlalchemy import paginate
from logging import getLogger

logger = getLogger(__name__)


class BaseTransactionsServiceError(Exception):
    """Base transactions service error."""


class TransactionsService:
    pass


def get_transactions_service() -> TransactionsService:
    return TransactionsService()
