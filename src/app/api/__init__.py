from fastapi import FastAPI, APIRouter, Depends

from app.api import docs
from app.api.admin import admin_api
from app.api.dependencies.tracing import store_request_meta_to_ctx
from app.api.internal import internal_api
from app.api.public import public_api

api_root = APIRouter(dependencies=[Depends(store_request_meta_to_ctx)])

api_root.include_router(public_api, prefix="", tags=["Public API"])
api_root.include_router(admin_api, prefix="/admin", tags=["Admin API"])
api_root.include_router(internal_api, prefix="/internal", tags=["Internal API"])
api_root.include_router(docs.router, prefix="/docs")


def init_api(app: FastAPI) -> None:
    app.include_router(api_root, prefix="/api")
