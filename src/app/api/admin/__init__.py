from fastapi import APIRouter, status, Depends

from app.api.admin import v1
from app.api.dependencies.auth import check_admin_role
from app.api.schemas import ErrorSchema

admin_api = APIRouter(
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_403_FORBIDDEN: {"model": ErrorSchema},
    },
    dependencies=[Depends(check_admin_role)],
)

admin_api.include_router(v1.receipts.router, prefix="/v1/receipts")
admin_api.include_router(v1.transactions.router, prefix="/v1/transactions")
