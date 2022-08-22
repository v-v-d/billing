from typing import Any
from unittest.mock import ANY, MagicMock
from uuid import UUID

import pytest
import sqlalchemy as sa
from aiohttp import BasicAuth
from async_asgi_testclient import TestClient
from pytest_mock import MockerFixture

from app.integrations.async_api import async_api_client
from app.integrations.yookassa import yookassa_client
from app.main import app
from app.models import Transaction
from app.models import UserFilm
from app.settings import settings
from app.transports import BaseTransportError
from tests.functional.utils import fake

pytestmark = pytest.mark.asyncio


@pytest.fixture
def film_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def active_user_film(db_session, valid_jwt_payload, film_id) -> None:
    stmt = sa.insert(UserFilm).values(
        user_id=valid_jwt_payload["user_id"],
        film_id=film_id,
        is_active=True,
    )
    await db_session.execute(stmt)


@pytest.fixture
def headers(valid_jwt_token) -> dict[str, Any]:
    return {
        "Authorization": valid_jwt_token,
        "Idempotence-Key": fake.cryptographic.uuid(),
    }


@pytest.fixture
def request_body() -> dict[str, Any]:
    return {"payment_type": Transaction.PaymentType.CARD.value}


@pytest.fixture
def mocked_async_api(request, mocker: MockerFixture) -> MagicMock:
    mock = {
        "id": "a801e84c-316a-4c0c-a5a5-cc024234b2cb",
        "rating": 6.5,
        "title": "Kre-O Star Trek",
        "description": "A stop-motion animated story about 'Star Trek' featuring Kre-O toy blocks.",
        "genres": [
            {
                "id": "6a0a479b-cfec-41ac-b520-41b2b007b611",
                "name": "Animation",
            },
            {
                "id": "a886d0ec-c3f3-4b16-b973-dedcf5bfa395",
                "name": "Short",
            },
        ],
        "directors": [],
        "actors": [],
        "writers": [],
        "actors_names": [],
        "writers_names": [],
        "directors_names": [],
        "price": request.param,
    }
    return mocker.patch.object(
        async_api_client.http_transport, "_request", return_value=mock
    )


@pytest.fixture
def failed_async_api(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(
        async_api_client.http_transport, "_request", side_effect=BaseTransportError()
    )


@pytest.fixture
def mocked_yookassa(mocker: MockerFixture) -> MagicMock:
    mock = {
        "id": "227cf565-000f-5000-8000-1c9d1c6000fb",
        "status": "succeeded",
        "paid": True,
        "amount": {"value": "600.00", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "confirmation_url": "https://yoomoney.ru/api-pages/v2/payment-confirm/epl?orderId=227cf565-000f-5000-8000-1c9d1c6000fb",
        },
        "authorization_details": {
            "rrn": "10000000000",
            "auth_code": "000000",
            "three_d_secure": {"applied": True},
        },
        "captured_at": "2018-05-03T10:17:31.487Z",
        "created_at": "2018-05-03T10:17:09.337Z",
        "metadata": {},
        "payment_method": {
            "type": "bank_card",
            "id": "227cf565-000f-5000-8000-1c9d1c6000fb",
            "saved": False,
            "card": {
                "first6": "411111",
                "last4": "1111",
                "expiry_month": "01",
                "expiry_year": "2020",
                "card_type": "Visa",
                "issuer_country": "RU",
                "issuer_name": "Sberbank",
            },
            "title": "Bank card *1111",
        },
        "receipt_registration": "pending",
        "recipient": {"account_id": "100500", "gateway_id": "100700"},
        "refundable": True,
        "refunded_amount": {"value": "600.00", "currency": "RUB"},
    }
    return mocker.patch.object(
        yookassa_client.http_transport, "_request", return_value=mock
    )


@pytest.fixture
def failed_yookassa(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(
        yookassa_client.http_transport, "_request", side_effect=BaseTransportError()
    )


@pytest.mark.parametrize("mocked_async_api", (30000, ), indirect=True)
async def test_ok(
    db_session,
    client: TestClient,
    valid_jwt_payload: dict[str, Any],
    headers: dict[str, Any],
    film_id: str,
    request_body: dict[str, Any],
    mocked_async_api: MagicMock,
    mocked_yookassa: MagicMock,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="purchase", film_id=film_id),
        headers=headers,
        json=request_body,
    )

    assert response.status_code == 200, response.text
    assert (
        response.json()["confirmation_url"]
        == mocked_yookassa.return_value["confirmation"]["confirmation_url"]
    )

    mocked_async_api.assert_called_with(
        method="GET",
        url=f"{settings.ASYNC_API_INTEGRATION.BASE_URL}/api/v1/films/{film_id}",
        timeout=settings.ASYNC_API_INTEGRATION.TIMEOUT_SEC,
    )
    mocked_yookassa.assert_called_with(
        method="POST",
        json={
            "amount": {"value": "300.00", "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": ANY,
            },
        },
        headers={"Idempotence-Key": UUID(headers["Idempotence-Key"])},
        auth=(
            BasicAuth(
                login=settings.YOOKASSA_INTEGRATION.AUTH_USER,
                password=settings.YOOKASSA_INTEGRATION.AUTH_PASSWORD,
                encoding="latin1",
            ),
        ),
    )

    stmt = sa.select(UserFilm).where(
        UserFilm.user_id == valid_jwt_payload["user_id"],
        UserFilm.film_id == film_id,
    )
    result = await db_session.execute(stmt)
    user_film = result.scalar()

    assert not user_film.is_active
    assert not user_film.watched


@pytest.mark.parametrize("mocked_async_api", (30000, ), indirect=True)
async def test_already_purchased(
    client: TestClient,
    headers: dict[str, Any],
    active_user_film,
    film_id: str,
    request_body: dict[str, Any],
    mocked_async_api: MagicMock,
    mocked_yookassa: MagicMock,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="purchase", film_id=film_id),
        headers=headers,
        json=request_body,
    )

    assert response.status_code == 200, response.text
    assert not response.json()["confirmation_url"]

    mocked_async_api.assert_not_called()
    mocked_yookassa.assert_not_called()


@pytest.mark.parametrize("mocked_async_api", (0, -1), indirect=True)
async def test_lte_zero_price(
    client: TestClient,
    headers: dict[str, Any],
    film_id: str,
    request_body: dict[str, Any],
    mocked_async_api: MagicMock,
    mocked_yookassa: MagicMock,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="purchase", film_id=film_id),
        headers=headers,
        json=request_body,
    )

    assert response.status_code == 200, response.text
    assert not response.json()["confirmation_url"]

    mocked_async_api.assert_called_with(
        method="GET",
        url=f"{settings.ASYNC_API_INTEGRATION.BASE_URL}/api/v1/films/{film_id}",
        timeout=settings.ASYNC_API_INTEGRATION.TIMEOUT_SEC,
    )
    mocked_yookassa.assert_not_called()


async def test_failed_async_api(
    client: TestClient,
    headers: dict[str, Any],
    film_id: str,
    request_body: dict[str, Any],
    failed_async_api: MagicMock,
    mocked_yookassa: MagicMock,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="purchase", film_id=film_id),
        headers=headers,
        json=request_body,
    )

    assert response.status_code == 424, response.text
    assert response.json()["detail"] == "Async API service error."

    failed_async_api.assert_called_with(
        method="GET",
        url=f"{settings.ASYNC_API_INTEGRATION.BASE_URL}/api/v1/films/{film_id}",
        timeout=settings.ASYNC_API_INTEGRATION.TIMEOUT_SEC,
    )
    mocked_yookassa.assert_not_called()


@pytest.mark.parametrize("mocked_async_api", (30000, ), indirect=True)
async def test_failed_yookassa(
    client: TestClient,
    headers: dict[str, Any],
    film_id: str,
    request_body: dict[str, Any],
    mocked_async_api: MagicMock,
    failed_yookassa: MagicMock,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="purchase", film_id=film_id),
        headers=headers,
        json=request_body,
    )

    assert response.status_code == 424, response.text
    assert response.json()["detail"] == "Yookassa service error."

    mocked_async_api.assert_called_with(
        method="GET",
        url=f"{settings.ASYNC_API_INTEGRATION.BASE_URL}/api/v1/films/{film_id}",
        timeout=settings.ASYNC_API_INTEGRATION.TIMEOUT_SEC,
    )
    failed_yookassa.assert_called_with(
        method="POST",
        json={
            "amount": {"value": "300.00", "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": ANY,
            },
        },
        headers={"Idempotence-Key": UUID(headers["Idempotence-Key"])},
        auth=(
            BasicAuth(
                login=settings.YOOKASSA_INTEGRATION.AUTH_USER,
                password=settings.YOOKASSA_INTEGRATION.AUTH_PASSWORD,
                encoding="latin1",
            ),
        ),
    )
