import http
from typing import Any

import pytest

from app.integrations.yookassa import YookassaHttpClient
from app.main import app

from tests.functional.utils import fake

from pytest_mock import MockerFixture

pytestmark = pytest.mark.asyncio


@pytest.fixture
def payment_data() -> dict[str, Any]:
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
def mocked_yookassa_answer() -> dict[str, Any]:
    return {"id": fake.cryptographic.uuid(), "status": "succeeded", "paid": True}


async def test_yookassa_notification(
    client, payment_data, mocked_yookassa_answer, mocker
) -> None:
    mocker.patch.object(
        YookassaHttpClient,
        "request",
        return_value=mocked_yookassa_answer,
    )

    response = await client.post(
        path=app.url_path_for(name="on_after_payment"),
        json=payment_data
    )
    assert response.status_code == 200, response.text
