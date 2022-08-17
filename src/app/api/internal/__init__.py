from fastapi import APIRouter

from app.api.internal import v1

internal_api = APIRouter()

internal_api.include_router(v1.users_films.router, prefix="/v1")
