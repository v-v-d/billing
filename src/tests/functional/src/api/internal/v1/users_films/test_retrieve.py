import http
from unittest.mock import ANY

import pytest

from app.api.errors import USER_FILM_NOT_FOUND
from app.main import app
from tests.functional.utils import fake

pytestmark = pytest.mark.asyncio


async def test_ok(client, user_film, user_id, film_id) -> None:
    response = await client.get(
        path=app.url_path_for(
            name="retrieve",
            user_id=user_id,
            film_id=film_id,
        ),
    )
    assert response.status_code == http.HTTPStatus.OK, response.text

    expected = {
        "id": ANY,
        "user_id": user_id,
        "film_id": film_id,
        "is_active": False,
        "watched": ANY,
    }
    assert response.json() == expected


async def test_not_found(client) -> None:
    response = await client.get(
        path=app.url_path_for(
            name="retrieve",
            user_id=fake.cryptographic.uuid(),
            film_id=fake.cryptographic.uuid(),
        ),
    )
    assert response.status_code == http.HTTPStatus.BAD_REQUEST, response.text
    assert response.json()["detail"] == USER_FILM_NOT_FOUND
