from fastapi import APIRouter

from app.api.internal import v1

internal_api = APIRouter()

internal_api.include_router(v1.transactions.router, prefix="/v1/transactions")
internal_api.include_router(v1.receipts.router, prefix="/v1/receipts")
