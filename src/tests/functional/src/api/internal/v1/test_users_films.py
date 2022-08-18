from unittest.mock import ANY

import pytest
import sqlalchemy as sa

from app.main import app
from app.models import UserFilm
from tests.functional.utils import fake

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def user_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def film_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def price() -> str:
    return fake.numeric.integer_number(start=300, end=400)


@pytest.fixture
async def user_film(db_session, user_id, film_id, price) -> None:
    stmt = sa.insert(UserFilm).values(
        user_id=user_id,
        film_id=film_id,
        price=price,
    )
    await db_session.execute(stmt)


async def test_ok(client, user_film, user_id, film_id, price) -> None:
    response = await client.put(
        path=app.url_path_for(
            name="mark_as_watched",
            user_id=user_id,
            film_id=film_id,
        ),
    )
    assert response.status_code == 200, response.text

    expected = {
        "id": ANY,
        "user_id": user_id,
        "film_id": film_id,
        "price": price,
        "is_active": True,
        "watched": True,
    }
    assert response.json() == expected


async def test_not_found(client) -> None:
    response = await client.put(
        path=app.url_path_for(
            name="mark_as_watched",
            user_id=fake.cryptographic.uuid(),
            film_id=fake.cryptographic.uuid(),
        ),
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Film not found for user specified"
