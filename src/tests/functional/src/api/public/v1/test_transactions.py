from typing import Any
import sqlalchemy as sa

import pytest

from app.main import app
from app.models import Transaction, Receipt

from tests.functional.utils import fake


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def user_id() -> str:
    return fake.cryptographic.uuid()


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
def headers(valid_jwt_token) -> dict[str, Any]:
    return {
        "Authorization": valid_jwt_token,
        "Idempotence-Key": fake.cryptographic.uuid(),
    }


@pytest.fixture
def headers_admin(valid_admin_token) -> dict[str, Any]:
    return {
        "Authorization": valid_admin_token,
        "Idempotence-Key": fake.cryptographic.uuid(),
    }


@pytest.fixture
async def db_data(
    db_session, transaction_id, transaction_ext_id, receipt_id, valid_jwt_payload
) -> None:

    stmt2 = sa.delete(Receipt)
    await db_session.execute(stmt2)
    stmt1 = sa.delete(Transaction)
    await db_session.execute(stmt1)

    stmt1 = sa.insert(Transaction).values(
        id=transaction_id,
        ext_id=transaction_ext_id,
        user_id=valid_jwt_payload["user_id"],
        amount=400,
        type=Transaction.TypeEnum.PAYMENT,
        payment_type=Transaction.PaymentType.CARD,
    )

    await db_session.execute(stmt1)

    stmt2 = sa.insert(Receipt).values(
        id=receipt_id,
        ext_id=transaction_ext_id,
        transaction_id=transaction_id,
    )
    await db_session.execute(stmt2)


@pytest.fixture
async def db_data_admin(
    db_session, transaction_id, transaction_ext_id, receipt_id, valid_admin_payload
) -> None:

    stmt2 = sa.delete(Receipt)
    await db_session.execute(stmt2)
    stmt1 = sa.delete(Transaction)
    await db_session.execute(stmt1)

    stmt1 = sa.insert(Transaction).values(
        id=transaction_id,
        ext_id=transaction_ext_id,
        user_id=valid_admin_payload["user_id"],
        amount=400,
        type=Transaction.TypeEnum.PAYMENT,
        payment_type=Transaction.PaymentType.CARD,
    )

    await db_session.execute(stmt1)

    stmt2 = sa.insert(Receipt).values(
        id=receipt_id,
        ext_id=transaction_ext_id,
        transaction_id=transaction_id,
    )
    await db_session.execute(stmt2)


async def test_user_transactions(
    client, headers, db_data, transaction_id, transaction_ext_id, valid_jwt_payload
) -> None:

    response = await client.get(
        path=app.url_path_for(name="get_users_transactions"),
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["id"] == transaction_id
    assert response.json()["items"][0]["ext_id"] == transaction_ext_id
    assert response.json()["items"][0]["amount"] == 400
    assert response.json()["items"][0]["user_id"] == valid_jwt_payload['user_id']


async def test_admin_transactions(
    client,
    headers_admin,
    db_data,
    transaction_id,
    transaction_ext_id,
) -> None:

    response = await client.get(
        path=app.url_path_for(name="get_transactions"), headers=headers_admin
    )

    assert response.status_code == 200, response.text
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["id"] == transaction_id
    assert response.json()["items"][0]["ext_id"] == transaction_ext_id
    assert response.json()["items"][0]["amount"] == 400


async def test_transaction_by_id(
    client,
    headers,
    db_data,
    transaction_id,
    transaction_ext_id,
    receipt_id,
) -> None:
    response = await client.get(
        path=app.url_path_for(
            name="get_transaction_by_id", transaction_id=transaction_id
        ),
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["id"] == transaction_id
    assert response.json()["ext_id"] == transaction_ext_id
    assert response.json()["receipts"][0]["id"] == receipt_id
    assert response.json()["amount"] == 400
