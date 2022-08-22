from fastapi import APIRouter, status, Depends

from app.api.dependencies.auth import decode_jwt
from app.api.public import v1
from app.api.schemas import ErrorSchema

public_api = APIRouter(
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_403_FORBIDDEN: {"model": ErrorSchema},
    }
)

public_api.include_router(v1.receipts.router, prefix="/v1/receipts")
public_api.include_router(v1.transactions.router, prefix="/v1/transactions")
public_api.include_router(v1.notifications.router, prefix="/v1/notifications")
