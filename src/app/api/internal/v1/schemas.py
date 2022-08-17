from pydantic import BaseModel, UUID4


class UserFilmOutputSchema(BaseModel):
    id: UUID4
    user_id: UUID4
    film_id: UUID4
    price: int
    watched: bool
    is_active: bool

    class Config:
        orm_mode = True
