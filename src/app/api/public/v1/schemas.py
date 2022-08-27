from typing import Optional

from app.api.schemas import ORJSONModel
from app.models import Transaction, Receipt, ReceiptItem
from pydantic import UUID4


class PaymentObjectSchema(ORJSONModel):
    id: UUID4
    status: str
    paid: bool


class PaymentNotificationSchema(ORJSONModel):
    type: str
    event: str
    object: PaymentObjectSchema


class PurchaseRequestSchema(ORJSONModel):
    payment_type: Transaction.PaymentType


class PurchaseResponseSchema(ORJSONModel):
    confirmation_url: Optional[str] = None


class UserFilmSchema(ORJSONModel):
    id: UUID4
    user_id: UUID4
    film_id: UUID4
    watched: bool
    is_active: bool

    class Config:
        orm_mode = True


class ReceiptItemSchema(ORJSONModel):
    id: UUID4
    description: str
    quantity: float
    amount: float
    type: ReceiptItem.TypeEnum

    class Config:
        orm_mode = True


class ReceiptSchema(ORJSONModel):
    id: UUID4
    status: Receipt.StatusEnum
    items: list[ReceiptItemSchema]

    class Config:
        orm_mode = True


class TransactionSchema(ORJSONModel):
    id: UUID4
    user_id: UUID4
    amount: float
    type: Transaction.TypeEnum
    status: Transaction.StatusEnum
    payment_type: Transaction.PaymentType
    receipt: ReceiptSchema
    user_film: Optional[UserFilmSchema]

    class Config:
        orm_mode = True
