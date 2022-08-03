import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class ORJSONModel(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class ErrorSchema(ORJSONModel):
    detail: str


class ResultSchema(ORJSONModel):
    result: bool = True


class DefaultSuccessResponse(ORJSONModel):
    content: ResultSchema = ResultSchema(result=True)
