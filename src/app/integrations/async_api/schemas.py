from app.api.schemas import ORJSONModel


class FilmSchema(ORJSONModel):
    title: str
    price: int
