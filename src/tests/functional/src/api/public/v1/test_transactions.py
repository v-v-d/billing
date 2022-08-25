from typing import Any
import sqlalchemy as sa

import pytest
from sqlalchemy.orm import selectinload

from app.integrations.yookassa import YookassaHttpClient
from app.main import app
from app.models import UserFilm, Transaction, Receipt

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
async def db_data(
    db_session, transaction_id, transaction_ext_id, receipt_id, valid_jwt_payload
) -> None:
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


async def test_transactions_by_id(
    client,
    valid_jwt_payload,
    valid_jwt_token,
    headers,
    db_session,
    db_data,
    transaction_id,
) -> None:

    print(
        "--- path: {}".format(
            app.url_path_for(
                name="get_transaction_by_id", transaction_id=transaction_id
            )
        )
    )
    response = await client.get(
        path=app.url_path_for(
            name="get_transaction_by_id", transaction_id=transaction_id
        ),
        headers=headers,
        json={"query": valid_jwt_token},
    )

    print("--- response: {}".format(response.text))
    assert response.status_code == 200, response.text
