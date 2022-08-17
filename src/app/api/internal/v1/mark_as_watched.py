
from fastapi import APIRouter
from pydantic import UUID4

from models import UserFilm

router = APIRouter()


@router.put("/users/{user_id}/films/{film_id}/mark-as-watched", description="Marks the film as watched")
async def mark_as_watched(
    user_id: UUID4, film_id: UUID4, db_session: AsyncSession = Depends(get_db)
):
    try:
        await UserFilm.mark_as_watched(
            session=db_session, user_id=user_id, film_id=film_id
        )
    except ObjectDoesNotExistError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Film not found for user specified"
        )
