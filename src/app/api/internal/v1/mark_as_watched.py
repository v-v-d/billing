from fastapi import APIRouter
from pydantic import UUID4

router = APIRouter()


@router.get("/users/{user_id}/films/{film_id}", description="Marks the film as watched")
async def get_transaction_by_id(
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
