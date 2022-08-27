import http
from typing import Any

import pytest
from furl import furl

from tests.functional.src.api.utils import LIMIT_QTY, OFFSET_NUM

pytestmark = pytest.mark.asyncio


@pytest.fixture
def path() -> str:
    return (
        furl("/api/v1/transactions")
        .add(query_params={"limit": LIMIT_QTY, "offset": OFFSET_NUM})
        .url
    )


@pytest.fixture
def expected_response(expected_retrieve) -> dict[str, Any]:
    return {
        "items": [expected_retrieve],
        "total": 1,
        "limit": LIMIT_QTY,
        "offset": OFFSET_NUM,
    }


async def test_ok(
    client,
    path,
    receipt_items,
    users_films,
    user_receipt_item,
    user_film,
    headers,
    expected_response,
) -> None:
    response = await client.get(
        path=path,
        headers=headers,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.json() == expected_response


async def test_not_target_user(
    client,
    path,
    receipt_items,
    users_films,
    user_receipt_item,
    user_film,
    not_target_headers,
) -> None:
    response = await client.get(
        path=path,
        headers=not_target_headers,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": LIMIT_QTY,
        "offset": OFFSET_NUM,
    }
