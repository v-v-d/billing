from pydantic import UUID4

from app.api.schemas import ORJSONModel


class UserFilmOutputSchema(ORJSONModel):
    id: UUID4
    user_id: UUID4
    film_id: UUID4
    watched: bool
    is_active: bool

    class Config:
        orm_mode = True
