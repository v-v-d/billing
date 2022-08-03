import asyncio
from functools import wraps
from typing import Callable, Any

import typer
import uvicorn
from IPython import embed

from app.settings import settings

typer_app = typer.Typer()


def coro(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@typer_app.command()
def shell():
    embed()


@typer_app.command()
def runserver():
    uvicorn.run(**settings.UVICORN.dict())


if __name__ == "__main__":
    typer_app()
