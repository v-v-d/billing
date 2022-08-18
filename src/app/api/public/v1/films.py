import uuid

from fastapi import APIRouter, Request, Depends, status
from pydantic import BaseModel
from uuid import UUID
from app.integrations.auth import auth_client
from app.security import get_id_user_from_token
from app.models import UserFilm, Transaction
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.database import get_db
import sqlalchemy as sa


router = APIRouter()


class Order(BaseModel):
    film_id: UUID


class ObjectAlreadyExistError(Exception):
    """Raise it if object already exist in database."""


@router.post("/{film_id}/purchase")
async def root(
    film_id: str, request: Request, db_session: AsyncSession = Depends(get_db)
):
    token = request.headers.get("Authorization").removeprefix("Bearer ")

    # TODO НЕ РАБОТАЕТ ручка в Auth /users/info (где по токену получаем юзера) или я что-то не так делаю
    # пока так посмотрите пожалуйста
    user_id = get_id_user_from_token(token)
    user = await auth_client.get_user_details(user_id)

    stmt = sa.select(UserFilm).where(
        sa.and_(UserFilm.film_id == film_id, UserFilm.user_id == user_id)
    )
    result = await db_session.execute(stmt)
    user_film_info = result.scalar()
    if user_film_info:
        return status.HTTP_200_OK

    # TODO Нужно сходить в AsyncAPI пока не могу поднять
    price = 50 * 100  # цена в копейках

    transaction = Transaction()
    curent_transaction = await transaction.create(
        db_session=db_session,
        ext_id=str(uuid.uuid4()),
        user_id=user_id,
        amount=price,
    )

    return await curent_transaction
