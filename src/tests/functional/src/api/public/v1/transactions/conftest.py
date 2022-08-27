from decimal import Decimal
from typing import Any

import pytest
from jose import jwt

from app.models import Transaction, Receipt, ReceiptItem, UserFilm
from app.settings import settings
from tests.functional.utils import fake


@pytest.fixture
def not_target_jwt_payload() -> dict[str, Any]:
    return {
        "user_id": fake.cryptographic.uuid(),
        "login": fake.person.full_name(),
        "email": fake.person.email(),
        "is_admin": False,
        "roles": [],
    }


@pytest.fixture
def not_target_jwt_token(not_target_jwt_payload) -> str:
    token = jwt.encode(
        not_target_jwt_payload,
        settings.SECURITY.JWT_AUTH.SECRET_KEY,
        algorithm=settings.SECURITY.JWT_AUTH.ALGORITHM,
    )

    return f"Bearer {token}"


@pytest.fixture
def not_target_headers(not_target_jwt_token) -> dict[str, Any]:
    return {
        "Authorization": not_target_jwt_token,
        "Idempotence-Key": fake.cryptographic.uuid(),
    }


@pytest.fixture
def user_transaction(db_session, valid_jwt_payload) -> Transaction:
    transaction = Transaction(
        id=fake.cryptographic.uuid(),
        ext_id=fake.cryptographic.uuid(),
        user_id=valid_jwt_payload["user_id"],
        amount=fake.numeric.integer_number(start=300, end=500),
        type=fake.choice([Transaction.TypeEnum.PAYMENT, Transaction.TypeEnum.REFUND]),
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
    db_session.add(transaction)

    return transaction


@pytest.fixture
def user_receipt(db_session, user_transaction: Transaction) -> Receipt:
    receipt = Receipt(
        id=fake.cryptographic.uuid(),
        ext_id=fake.cryptographic.uuid(),
        transaction_id=user_transaction.id,
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
    db_session.add(receipt)

    return receipt


@pytest.fixture
def user_receipt_item(db_session, user_receipt: Receipt) -> ReceiptItem:
    receipt_item = ReceiptItem(
        id=fake.cryptographic.uuid(),
        receipt_id=user_receipt.id,
        description=fake.text.word(),
        quantity=fake.numeric.decimal_number(start=1, end=3),
        amount=fake.numeric.decimal_number(start=300, end=500),
        type=fake.choice(
            [ReceiptItem.TypeEnum.FILM, ReceiptItem.TypeEnum.SUBSCRIPTION]
        ),
    )
    db_session.add(receipt_item)

    return receipt_item


@pytest.fixture
def user_film(db_session, user_transaction: Transaction) -> UserFilm:
    user_film = UserFilm(
        id=fake.cryptographic.uuid(),
        transaction_id=user_transaction.id,
        user_id=user_transaction.user_id,
        film_id=fake.cryptographic.uuid(),
        watched=fake.choice([True, False]),
        is_active=fake.choice([True, False]),
    )
    db_session.add(user_film)

    return user_film


@pytest.fixture
def expected_retrieve(
    user_transaction: Transaction,
    user_receipt: Receipt,
    user_receipt_item: ReceiptItem,
    user_film: UserFilm,
) -> dict[str, Any]:
    return {
        "id": user_transaction.id,
        "user_id": user_transaction.user_id,
        "amount": round(float(user_transaction.amount), 1),
        "type": user_transaction.type.value,
        "status": user_transaction.status.value,
        "payment_type": user_transaction.payment_type.value,
        "receipt": {
            "id": user_receipt.id,
            "status": user_receipt.status.value,
            "items": [
                {
                    "id": user_receipt_item.id,
                    "description": user_receipt_item.description,
                    "quantity": float(
                        user_receipt_item.quantity.quantize(Decimal(".001"))
                    ),
                    "amount": float(user_receipt_item.amount.quantize(Decimal(".001"))),
                    "type": user_receipt_item.type.value,
                }
            ],
        },
        "user_film": {
            "id": user_film.id,
            "user_id": user_film.user_id,
            "film_id": user_film.film_id,
            "watched": user_film.watched,
            "is_active": user_film.is_active,
        },
    }
