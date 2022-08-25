from typing import Any
from unittest.mock import ANY, MagicMock
from uuid import UUID

import pytest
import sqlalchemy as sa
from aiohttp import BasicAuth
from async_asgi_testclient import TestClient
from jose import jwt
from pytest_mock import MockerFixture

from app.integrations.yookassa import yookassa_client, StatusEnum
from app.main import app
from app.models import Transaction, Receipt, ReceiptItem
from app.models import UserFilm
from app.settings import settings
from app.transports import BaseTransportError
from tests.functional.utils import fake

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def not_target_jwt_token() -> str:
    token = jwt.encode(
        {
            "user_id": fake.cryptographic.uuid(),
            "login": fake.person.full_name(),
            "email": fake.person.email(),
            "is_admin": False,
            "roles": [],
        },
        settings.SECURITY.JWT_AUTH.SECRET_KEY,
        algorithm=settings.SECURITY.JWT_AUTH.ALGORITHM,
    )

    return f"Bearer {token}"


@pytest.fixture
async def transaction_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def receipt_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def transaction_ext_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def film_price() -> str:
    return fake.numeric.integer_number(start=50, end=500)


@pytest.fixture
async def film_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def user_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def payment_receipt(
    db_session,
    receipt_id,
    transaction_id,
) -> None:
    stmt = sa.insert(Receipt).values(
        id=receipt_id,
        ext_id=fake.cryptographic.uuid(),
        transaction_id=transaction_id,
        status=Receipt.StatusEnum.CREATED,
    )
    await db_session.execute(stmt)


@pytest.fixture
async def payment_receipt_item(
    db_session,
    receipt_id,
) -> None:
    stmt = sa.insert(ReceiptItem).values(
        id=fake.cryptographic.uuid(),
        receipt_id=receipt_id,
        description=fake.text.word(),
        quantity=fake.numeric.decimal_number(start=1, end=3),
        amount=fake.numeric.decimal_number(start=300, end=500),
        type=ReceiptItem.TypeEnum.FILM,
    )
    await db_session.execute(stmt)


@pytest.fixture
async def payment_transaction(
    request,
    db_session,
    valid_jwt_payload,
    transaction_id,
    transaction_ext_id,
    film_price,
) -> None:
    stmt = sa.insert(Transaction).values(
        id=transaction_id,
        ext_id=transaction_ext_id,
        user_id=valid_jwt_payload["user_id"],
        amount=film_price,
        type=Transaction.TypeEnum.PAYMENT,
        payment_type=Transaction.PaymentType.CARD,
        status=request.param,
    )
    await db_session.execute(stmt)


@pytest.fixture
async def payment_transaction_wo_ext_id(
    db_session,
    valid_jwt_payload,
    transaction_id,
    film_price,
) -> None:
    stmt = sa.insert(Transaction).values(
        id=transaction_id,
        user_id=valid_jwt_payload["user_id"],
        amount=film_price,
        type=Transaction.TypeEnum.PAYMENT,
        payment_type=Transaction.PaymentType.CARD,
        status=Transaction.StatusEnum.SUCCEEDED,
    )
    await db_session.execute(stmt)


@pytest.fixture
async def user_film(
    request,
    db_session,
    valid_jwt_payload,
    film_id,
    transaction_id,
) -> None:
    is_active, watched = request.param
    stmt = sa.insert(UserFilm).values(
        user_id=valid_jwt_payload["user_id"],
        film_id=film_id,
        is_active=is_active,
        watched=watched,
        transaction_id=transaction_id,
    )
    await db_session.execute(stmt)


@pytest.fixture
def headers(valid_jwt_token) -> dict[str, Any]:
    return {
        "Authorization": valid_jwt_token,
        "Idempotence-Key": fake.cryptographic.uuid(),
    }


@pytest.fixture
def mocked_yookassa(request, mocker: MockerFixture, transaction_ext_id) -> MagicMock:
    mock = {
        "id": "216749f7-0016-50be-b000-078d43a63ae4",
        "status": request.param,
        "amount": {"value": "2.00", "currency": "RUB"},
        "created_at": "2017-10-04T19:27:51.407Z",
        "payment_id": transaction_ext_id,
    }

    if request.param == StatusEnum.CANCELED.value:
        mock["cancellation_details"] = {
            "party": "yoo_money",
            "reason": "insufficient_funds",
        }

    return mocker.patch.object(
        yookassa_client.http_transport, "_request", return_value=mock
    )


@pytest.fixture
def failed_yookassa(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(
        yookassa_client.http_transport, "_request", side_effect=BaseTransportError()
    )


@pytest.fixture
def expected_response(
    payment_receipt,
    payment_receipt_item,
    valid_jwt_payload,
    film_price,
    film_id,
) -> dict[str, Any]:
    return {
        "id": ANY,
        "user_id": valid_jwt_payload["user_id"],
        "amount": float(film_price),
        "type": Transaction.TypeEnum.REFUND.value,
        "status": ANY,
        "payment_type": ANY,
        "receipt": {
            "id": ANY,
            "status": Receipt.StatusEnum.CREATED.value,
            "items": [
                {
                    "id": ANY,
                    "description": ANY,
                    "quantity": ANY,
                    "amount": ANY,
                    "type": ReceiptItem.TypeEnum.FILM.value,
                }
            ],
        },
        "user_film": {
            "id": ANY,
            "user_id": valid_jwt_payload["user_id"],
            "film_id": film_id,
            "watched": False,
            "is_active": False,
        },
    }


@pytest.mark.parametrize(
    "payment_transaction,user_film,mocked_yookassa",
    [(Transaction.StatusEnum.SUCCEEDED, (True, False), StatusEnum.SUCCEEDED.value)],
    indirect=True,
)
async def test_ok(
    db_session,
    client: TestClient,
    valid_jwt_payload: dict[str, Any],
    headers: dict[str, Any],
    transaction_id: str,
    payment_transaction,
    payment_receipt,
    payment_receipt_item,
    user_film,
    film_id,
    mocked_yookassa: MagicMock,
    expected_response: dict[str, Any],
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json() == expected_response

    mocked_yookassa.assert_called_with(
        method="POST",
        url=f"{settings.YOOKASSA_INTEGRATION.BASE_URL}/v3/refunds",
        json={
            "amount": {
                "value": ANY,
                "currency": "RUB",
            },
            "payment_id": ANY,
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


async def test_payment_not_found(client, headers) -> None:
    response = await client.post(
        path=app.url_path_for(
            name="refund",
            transaction_id=fake.cryptographic.uuid(),
        ),
        headers=headers,
    )

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Unknown transaction."


@pytest.mark.parametrize(
    "payment_transaction",
    (Transaction.StatusEnum.SUCCEEDED,),
    indirect=True,
)
async def test_permission_denied(
    client,
    not_target_jwt_token,
    transaction_id,
    payment_transaction,
) -> None:
    headers = {
        "Authorization": not_target_jwt_token,
        "Idempotence-Key": fake.cryptographic.uuid(),
    }
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Permission denied."


@pytest.mark.parametrize(
    "payment_transaction",
    (Transaction.StatusEnum.CREATED,),
    indirect=True,
)
async def test_incorrect_payment_status(
    client,
    headers,
    transaction_id,
    payment_transaction,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Incorrect transaction status."


async def test_payment_has_no_ext_id(
    client, headers, payment_transaction_wo_ext_id, transaction_id
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Not available for refund."


@pytest.mark.parametrize(
    "payment_transaction",
    (Transaction.StatusEnum.SUCCEEDED,),
    indirect=True,
)
async def test_payment_has_no_user_film(
    client, headers, transaction_id, payment_transaction
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Not available for refund."


@pytest.mark.parametrize(
    "payment_transaction,user_film",
    [(Transaction.StatusEnum.SUCCEEDED, (False, False))],
    indirect=True,
)
async def test_user_film_already_inactive(
    client,
    headers,
    payment_transaction,
    transaction_id,
    user_film,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Not available for refund."


@pytest.mark.parametrize(
    "payment_transaction,user_film",
    [(Transaction.StatusEnum.SUCCEEDED, (True, True))],
    indirect=True,
)
async def test_user_film_already_watched(
    client, headers, transaction_id, payment_transaction, user_film
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "Not available because the film has already been watched."
    )


@pytest.mark.parametrize(
    "payment_transaction,user_film,mocked_yookassa",
    [(Transaction.StatusEnum.SUCCEEDED, (True, False), StatusEnum.CANCELED.value)],
    indirect=True,
)
async def test_bad_yookassa_status(
    client: TestClient,
    valid_jwt_payload: dict[str, Any],
    headers: dict[str, Any],
    transaction_id: str,
    payment_transaction,
    payment_receipt,
    payment_receipt_item,
    user_film,
    film_id,
    mocked_yookassa: MagicMock,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 424, response.text
    assert (
        response.json()["detail"]
        == "Operation rejected. Please contact technical support."
    )


@pytest.mark.parametrize(
    "payment_transaction,user_film",
    [(Transaction.StatusEnum.SUCCEEDED, (True, False))],
    indirect=True,
)
async def test_failed_yookassa(
    client: TestClient,
    valid_jwt_payload: dict[str, Any],
    headers: dict[str, Any],
    transaction_id: str,
    payment_transaction,
    payment_receipt,
    payment_receipt_item,
    user_film,
    film_id,
    failed_yookassa: MagicMock,
) -> None:
    response = await client.post(
        path=app.url_path_for(name="refund", transaction_id=transaction_id),
        headers=headers,
    )

    assert response.status_code == 424, response.text
    assert response.json()["detail"] == "Yookassa service error."
