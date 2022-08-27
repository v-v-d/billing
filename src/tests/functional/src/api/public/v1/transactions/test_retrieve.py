import http

import pytest
from furl import furl

from app.api.errors import TRANSACTION_NOT_FOUND, NOT_AUTHENTICATED
from tests.functional.utils import fake

pytestmark = pytest.mark.asyncio


@pytest.fixture
def path(user_transaction) -> str:
    return furl("/api/v1/transactions").add(path=user_transaction.id).url


async def test_ok(
    client,
    path,
    receipt_items,
    users_films,
    user_receipt_item,
    user_film,
    headers,
    expected_retrieve,
) -> None:
    response = await client.get(
        path=path,
        headers=headers,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.json() == expected_retrieve


async def test_not_found(
    client,
    receipt_items,
    users_films,
    headers,
) -> None:
    path = furl("/api/v1/transactions").add(path=fake.cryptographic.uuid()).url
    response = await client.get(
        path=path,
        headers=headers,
    )

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == TRANSACTION_NOT_FOUND


async def test_unauthorized(
    client,
    path,
    receipt_items,
    users_films,
) -> None:
    response = await client.get(path=path)

    assert response.status_code == http.HTTPStatus.UNAUTHORIZED
    assert response.json()["detail"] == NOT_AUTHENTICATED
