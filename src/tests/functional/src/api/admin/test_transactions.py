import http
from typing import Any
from unittest.mock import ANY

import pytest
from furl import furl

from tests.functional.src.api.utils import LIMIT_QTY, TRANSACTIONS_QTY, OFFSET_NUM

pytestmark = pytest.mark.asyncio


@pytest.fixture
def path() -> str:
    return (
        furl("/api/admin/v1/transactions")
        .add(query_params={"limit": LIMIT_QTY, "offset": OFFSET_NUM})
        .url
    )


@pytest.fixture
def invalid_headers(valid_jwt_token) -> dict[str, Any]:
    return {
        "Authorization": valid_jwt_token,
    }


@pytest.fixture
def valid_headers(valid_admin_token) -> dict[str, Any]:
    return {
        "Authorization": valid_admin_token,
    }


@pytest.fixture
def expected_response() -> dict[str, Any]:
    expected_items = [
        {
            "id": ANY,
            "user_id": ANY,
            "amount": ANY,
            "type": ANY,
            "status": ANY,
            "payment_type": ANY,
            "receipt": {
                "id": ANY,
                "status": ANY,
                "items": [
                    {
                        "id": ANY,
                        "description": ANY,
                        "quantity": ANY,
                        "amount": ANY,
                        "type": ANY,
                    }
                ],
            },
            "user_film": {
                "id": ANY,
                "user_id": ANY,
                "film_id": ANY,
                "watched": ANY,
                "is_active": ANY,
            },
        }
        for _ in range(LIMIT_QTY)
    ]

    return {
        "items": expected_items,
        "total": TRANSACTIONS_QTY,
        "limit": LIMIT_QTY,
        "offset": OFFSET_NUM,
    }


async def test_ok(
    client, path, receipt_items, users_films, valid_headers, expected_response
) -> None:
    response = await client.get(
        path=path,
        headers=valid_headers,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.json() == expected_response


async def test_forbidden(
    client, path, receipt_items, users_films, invalid_headers
) -> None:
    response = await client.get(
        path=path,
        headers=invalid_headers,
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
