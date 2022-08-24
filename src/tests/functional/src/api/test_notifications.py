from typing import Any
import sqlalchemy as sa

import pytest
from sqlalchemy.orm import selectinload

from app.integrations.yookassa import YookassaHttpClient
from app.main import app
from app.models import UserFilm, Transaction

from tests.functional.utils import fake

from pytest_mock import MockerFixture

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def user_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def transaction_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
async def transaction_ext_id() -> str:
    return fake.cryptographic.uuid()


@pytest.fixture
def payment_data_succeeded(transaction_ext_id) -> dict[str, Any]:
    return {
        "type": "notification",
        "event": "payment.waiting_for_capture",
        "object": {
            "id": transaction_ext_id,
            "status": "succeeded",
            "paid": True,
        },
    }


@pytest.fixture
def payment_data_wrong_transaction_id() -> dict[str, Any]:
    return {
        "type": "notification",
        "event": "payment.waiting_for_capture",
        "object": {
            "id": fake.cryptographic.uuid(),
            "status": "succeeded",
            "paid": True,
        },
    }


@pytest.fixture
def mocked_yookassa_answer_succeeded(transaction_ext_id) -> dict[str, Any]:
    return {"id": transaction_ext_id, "status": "succeeded", "paid": True}


@pytest.fixture
def mocked_yookassa_answer_canceled(transaction_ext_id) -> dict[str, Any]:
    return {"id": transaction_ext_id, "status": "canceled", "paid": True}


@pytest.fixture
def mocked_yookassa_answer_unavailable() -> dict[str, Any]:
    return {"result": 404}


@pytest.fixture
async def db_data(db_session, transaction_id, transaction_ext_id, user_id) -> None:
    stmt1 = sa.insert(Transaction).values(
        id=transaction_id,
        ext_id=transaction_ext_id,
        user_id=user_id,
        amount=400,
        type=Transaction.TypeEnum.PAYMENT,
        payment_type=Transaction.PaymentType.CARD,
    )

    await db_session.execute(stmt1)

    stmt2 = sa.insert(UserFilm).values(
        user_id=user_id,
        film_id=fake.cryptographic.uuid(),
        transaction_id=transaction_id,
        price=400,
        is_active=False,
    )
    await db_session.execute(stmt2)


async def test_yookassa_notification_payment_succeeded(
        client,
        db_session,
        db_data,
        payment_data_succeeded,
        mocked_yookassa_answer_succeeded,
        transaction_id,
        mocker,
) -> None:
    mocker.patch.object(
        YookassaHttpClient,
        "request",
        return_value=mocked_yookassa_answer_succeeded,
    )

    response = await client.post(
        path=app.url_path_for(name="on_after_payment"), json=payment_data_succeeded
    )

    assert response.status_code == 200, response.text

    stmt = sa.select(UserFilm).where(
        UserFilm.transaction_id == transaction_id,
    ).options(selectinload(UserFilm.transaction))

    result = await db_session.execute(stmt)
    user_film = result.scalar()

    assert user_film.is_active
    assert user_film.transaction.status == Transaction.StatusEnum.SUCCEEDED


async def test_yookassa_notification_payment_canceled(
        client,
        db_session,
        db_data,
        payment_data_succeeded,
        mocked_yookassa_answer_canceled,
        transaction_id,
        mocker,
) -> None:
    mocker.patch.object(
        YookassaHttpClient,
        "request",
        return_value=mocked_yookassa_answer_canceled,
    )

    response = await client.post(
        path=app.url_path_for(name="on_after_payment"), json=payment_data_succeeded
    )

    assert response.status_code == 200, response.text

    stmt = sa.select(UserFilm).where(
        UserFilm.transaction_id == transaction_id,
    ).options(selectinload(UserFilm.transaction))

    result = await db_session.execute(stmt)
    user_film = result.scalar()

    assert not user_film.is_active
    assert user_film.transaction.status == Transaction.StatusEnum.CREATED


async def test_yookassa_notification_failure(
        client,
        db_session,
        db_data,
        payment_data_succeeded,
        mocked_yookassa_answer_unavailable,
        transaction_id,
        mocker,
) -> None:
    mocker.patch.object(
        YookassaHttpClient,
        "request",
        return_value=mocked_yookassa_answer_unavailable,
    )

    response = await client.post(
        path=app.url_path_for(name="on_after_payment"), json=payment_data_succeeded
    )

    assert response.status_code == 424, response.text


async def test_yookassa_notification_wrong_id(
        client,
        payment_data_wrong_transaction_id,
        mocked_yookassa_answer_succeeded,
        transaction_id,
        mocker,
) -> None:
    mocker.patch.object(
        YookassaHttpClient,
        "request",
        return_value=mocked_yookassa_answer_succeeded,
    )

    response = await client.post(
        path=app.url_path_for(name="on_after_payment"),
        json=payment_data_wrong_transaction_id,
    )

    assert response.status_code == 200, response.text
