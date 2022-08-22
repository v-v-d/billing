from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db
from app.api.internal.v1.schemas import UserFilmOutputSchema
from app.api.schemas import ErrorSchema
from app.models import UserFilm, ObjectDoesNotExistError

router = APIRouter()


@router.put(
    "/users/{user_id}/films/{film_id}/mark-as-watched",
    response_model=UserFilmOutputSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
    },
    description="Marks the film as watched",
)
async def mark_as_watched(
    user_id: UUID4, film_id: UUID4, db_session: AsyncSession = Depends(get_db)
):
    try:
        user_film = await UserFilm.update(
            session=db_session, user_id=user_id, film_id=film_id, watched=True
        )
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Film not found for user specified",
        )

    return UserFilmOutputSchema.from_orm(user_film)


@router.get(
    "/users/{user_id}/films/{film_id}",
    response_model=UserFilmOutputSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorSchema},
    },
    description="Retrieve user film.",
)
async def retrieve(
    user_id: UUID4, film_id: UUID4, db_session: AsyncSession = Depends(get_db)
):
    try:
        user_film = await UserFilm.get(
            session=db_session, user_id=user_id, film_id=film_id
        )
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User film not found.",
        )

    return UserFilmOutputSchema.from_orm(user_film)
