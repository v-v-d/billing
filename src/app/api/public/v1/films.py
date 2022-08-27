from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.database import get_db
from app.api.errors import ASYNC_API_SERVICE_ERROR, YOOKASSA_SERVICE_ERROR
from app.api.public.v1.schemas import PurchaseResponseSchema, PurchaseRequestSchema
from app.security import TokenData
from app.services.payments.exceptions import (
    AlreadyPurchasedError,
    AsyncAPIUnavailableError,
    YookassaUnavailableError,
)
from app.services.payments.service import payments_service

router = APIRouter()


@router.post(
    "/{film_id}/purchase",
    response_model=PurchaseResponseSchema,
    description="Handle purchase request.",
)
async def purchase(
    film_id: str,
    body: PurchaseRequestSchema,
    idempotence_key: UUID4 = Header(),
    payload_data: TokenData = Depends(decode_jwt),
    db_session: AsyncSession = Depends(get_db),
):
    try:
        confirmation_url = await payments_service.purchase_film(
            db_session,
            payload_data.user_id,
            film_id,
            body.payment_type,
            idempotence_key,
        )
    except AlreadyPurchasedError:
        return PurchaseResponseSchema()

    except AsyncAPIUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=ASYNC_API_SERVICE_ERROR,
        )

    except YookassaUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=YOOKASSA_SERVICE_ERROR,
        )

    return PurchaseResponseSchema(confirmation_url=confirmation_url)
