import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.async_sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.database import get_db
from app.api.errors import (
    TRANSACTION_NOT_FOUND,
    PERMISSION_DENIED,
    INCORRECT_TRANSACTION_STATUS,
    REFUND_UNAVAILABLE,
    USER_FILM_ALREADY_WATCHED,
    REFUND_ERROR,
    YOOKASSA_SERVICE_ERROR,
)
from app.api.public.v1.schemas import TransactionSchema
from app.api.schemas import ErrorSchema
from app.models import Transaction, ObjectDoesNotExistError
from app.security import TokenData
from app.services.payments.exceptions import (
    PermissionDeniedError,
    IncorrectTransactionStatusError,
    NotAvalableForRefundError,
    AlreadyWatchedError,
    YookassaRefundError,
    YookassaUnavailableError,
)
from app.services.payments.service import payments_service

router = APIRouter()


@router.post(
    "/{transaction_id}/refund",
    response_model=TransactionSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_403_FORBIDDEN: {"model": ErrorSchema},
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorSchema},
        status.HTTP_424_FAILED_DEPENDENCY: {"model": ErrorSchema},
    },
    description="Handle refund request.",
)
async def refund(
    transaction_id: UUID4,
    idempotence_key: UUID4 = Header(),
    payload_data: TokenData = Depends(decode_jwt),
    db_session: AsyncSession = Depends(get_db),
):
    try:
        transaction = await payments_service.refund_film(
            db_session,
            transaction_id,
            payload_data.user_id,
            idempotence_key,
        )
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=TRANSACTION_NOT_FOUND,
        )

    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PERMISSION_DENIED,
        )

    except IncorrectTransactionStatusError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INCORRECT_TRANSACTION_STATUS,
        )

    except NotAvalableForRefundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=REFUND_UNAVAILABLE,
        )

    except AlreadyWatchedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=USER_FILM_ALREADY_WATCHED,
        )

    except YookassaRefundError:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=REFUND_ERROR,
        )

    except YookassaUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=YOOKASSA_SERVICE_ERROR,
        )

    return TransactionSchema.from_orm(transaction)


@router.get(
    "",
    response_model=LimitOffsetPage[TransactionSchema],
    description="Get list of user transactions",
)
async def get_list(
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt),
):
    return await paginate(
        db_session,
        sa.select(Transaction).where(Transaction.user_id == jwt_payload.user_id),
    )


@router.get(
    "/{transaction_id}",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
    },
    response_model=TransactionSchema,
    description="Retrieve transaction",
)
async def retrieve(
    transaction_id: UUID4,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt),
):
    try:
        transaction = await Transaction.get(
            db_session, id=transaction_id, user_id=jwt_payload.user_id
        )
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=TRANSACTION_NOT_FOUND
        )

    return TransactionSchema.from_orm(transaction)
