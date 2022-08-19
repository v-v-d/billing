from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db
from app.models import UserFilm, ObjectDoesNotExistError

router = APIRouter()


@router.post(
    "/yookassa/on-after-payment",
    description="Callback from yookassa",
    status_code=200
)
async def mark_as_watched(request: Request, db_session: AsyncSession = Depends(get_db)):
    message_body = await request.json()
    transaction_id = message_body.get("object", {}).get("id")
    transaction_status = message_body.get("object", {}).get("status")

    if not transaction_id or not transaction_status:
        return  # received notification is not about transaction status

    if "success" in transaction_status:
        try:
            await UserFilm.update_by_transaction(
                session=db_session, transaction_id=transaction_id, is_active=True
            )
        except ObjectDoesNotExistError:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="transaction not found"
            )

