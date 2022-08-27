from typing import Any

import pytest
from jose import jwt

from app.models import Transaction, Receipt, ReceiptItem, UserFilm
from app.settings import settings
from tests.functional.src.api.utils import TRANSACTIONS_QTY
from tests.functional.utils import fake


@pytest.fixture
def valid_jwt_payload() -> dict[str, Any]:
    return {
        "user_id": fake.cryptographic.uuid(),
        "login": fake.person.full_name(),
        "email": fake.person.email(),
        "is_admin": False,
        "roles": [],
    }


@pytest.fixture
def valid_jwt_token(valid_jwt_payload) -> str:
    token = jwt.encode(
        valid_jwt_payload,
        settings.SECURITY.JWT_AUTH.SECRET_KEY,
        algorithm=settings.SECURITY.JWT_AUTH.ALGORITHM,
    )

    return f"Bearer {token}"


@pytest.fixture
def valid_admin_payload() -> dict[str, Any]:
    return {
        "user_id": fake.cryptographic.uuid(),
        "login": fake.person.full_name(),
        "email": fake.person.email(),
        "is_admin": True,
        "roles": ["admin"],
    }


@pytest.fixture
def valid_admin_token(valid_admin_payload) -> str:
    token = jwt.encode(
        valid_admin_payload,
        settings.SECURITY.JWT_AUTH.SECRET_KEY,
        algorithm=settings.SECURITY.JWT_AUTH.ALGORITHM,
    )

    return f"Bearer {token}"


@pytest.fixture
def headers(valid_jwt_token) -> dict[str, Any]:
    return {
        "Authorization": valid_jwt_token,
        "Idempotence-Key": fake.cryptographic.uuid(),
    }


@pytest.fixture
def transactions(db_session) -> list[Transaction]:
    transactions = [
        Transaction(
            id=fake.cryptographic.uuid(),
            ext_id=fake.cryptographic.uuid(),
            user_id=fake.cryptographic.uuid(),
            amount=fake.numeric.integer_number(start=300, end=500),
            type=fake.choice(
                [Transaction.TypeEnum.PAYMENT, Transaction.TypeEnum.REFUND]
            ),
            payment_type=fake.choice(
                [
                    Transaction.PaymentType.CARD,
                    Transaction.PaymentType.APAY,
                    Transaction.PaymentType.GPAY,
                    Transaction.PaymentType.QR,
                ]
            ),
            status=fake.choice(
                [
                    Transaction.StatusEnum.CREATED,
                    Transaction.StatusEnum.PENDING,
                    Transaction.StatusEnum.WAITING_FOR_CAPTURE,
                    Transaction.StatusEnum.SUCCEEDED,
                    Transaction.StatusEnum.FAILED,
                    Transaction.StatusEnum.CANCELED,
                ]
            ),
        )
        for _ in range(TRANSACTIONS_QTY)
    ]
    db_session.add_all(transactions)

    return transactions


@pytest.fixture
def receipts(db_session, transactions: list[Transaction]) -> list[Receipt]:
    receipts = [
        Receipt(
            id=fake.cryptographic.uuid(),
            ext_id=fake.cryptographic.uuid(),
            transaction_id=transaction.id,
            status=fake.choice(
                [
                    Receipt.StatusEnum.CREATED,
                    Receipt.StatusEnum.FAILED,
                    Receipt.StatusEnum.PENDING,
                    Receipt.StatusEnum.SUCCEEDED,
                    Receipt.StatusEnum.CANCELED,
                ]
            ),
        )
        for transaction in transactions
    ]
    db_session.add_all(receipts)

    return receipts


@pytest.fixture
def receipt_items(db_session, receipts: list[Receipt]) -> list[ReceiptItem]:
    receipt_items = [
        ReceiptItem(
            id=fake.cryptographic.uuid(),
            receipt_id=receipt.id,
            description=fake.text.word(),
            quantity=fake.numeric.decimal_number(start=1, end=3),
            amount=fake.numeric.decimal_number(start=300, end=500),
            type=fake.choice(
                [ReceiptItem.TypeEnum.FILM, ReceiptItem.TypeEnum.SUBSCRIPTION]
            ),
        )
        for receipt in receipts
    ]
    db_session.add_all(receipt_items)

    return receipt_items


@pytest.fixture
def users_films(db_session, transactions: list[Transaction]) -> list[UserFilm]:
    users_films = [
        UserFilm(
            id=fake.cryptographic.uuid(),
            transaction_id=transaction.id,
            user_id=transaction.user_id,
            film_id=fake.cryptographic.uuid(),
            watched=fake.choice([True, False]),
            is_active=fake.choice([True, False]),
        )
        for transaction in transactions
    ]
    db_session.add_all(users_films)

    return users_films
