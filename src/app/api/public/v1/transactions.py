import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.async_sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.database import get_db
from app.api.admin.v1.schemas import TransactionOutput
from app.api.public.v1.schemas import TransactionSchema
from app.api.schemas import ErrorSchema
from app.models import Transaction, ObjectDoesNotExistError
from app.security import TokenData
from app.services.payments import (
    payments_service,
    YookassaUnavailableError,
    PermissionDeniedError,
    NotAvalableForRefundError,
    IncorrectTransactionStatusError,
    AlreadyWatchedError,
    YookassaRefundError,
)

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
            detail="Unknown transaction.",
        )

    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied.",
        )

    except IncorrectTransactionStatusError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect transaction status.",
        )

    except NotAvalableForRefundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not available for refund.",
        )

    except AlreadyWatchedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not available because the film has already been watched.",
        )

    except YookassaRefundError:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Operation rejected. Please contact technical support.",
        )

    except YookassaUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Yookassa service error.",
        )

    return TransactionSchema.from_orm(transaction)


@router.get(
    "/",
    response_model=LimitOffsetPage[TransactionOutput],
    description="Retrieve user transactions",
)
async def get_users_transactions(
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt),
):
    user_id = jwt_payload.user_id
    return await paginate(
        db_session,
        sa.select(Transaction)
        .where(Transaction.user_id == user_id)
        .options(selectinload(Transaction.receipt))
        .options(selectinload(Transaction.user_film)),
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionOutput,
    description="Retrieve transaction",
)
async def get_transaction_by_id(
    transaction_id: UUID4,
    db_session: AsyncSession = Depends(get_db),
    jwt_payload: TokenData = Depends(decode_jwt),
):
    user_id = jwt_payload.user_id

    try:
        template = await Transaction.get(db_session, id=transaction_id, user_id=user_id)
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return TransactionOutput.from_orm(template)
