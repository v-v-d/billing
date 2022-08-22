import pytest
import sqlalchemy as sa

from app.models import UserFilm
from tests.functional.utils import fake


@pytest.fixture
async def user_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def film_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def user_film(db_session, user_id, film_id) -> None:
    stmt = sa.insert(UserFilm).values(
        user_id=user_id,
        film_id=film_id,
    )
    await db_session.execute(stmt)
