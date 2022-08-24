from typing import Optional

from app.api.schemas import ORJSONModel
from app.models import Transaction
from pydantic import BaseModel, UUID4


class PaymentObjectSchema(BaseModel):
    id: UUID4
    status: str
    paid: bool


class PaymentNotificationSchema(BaseModel):
    type: str
    event: str
    object: PaymentObjectSchema


class PurchaseRequestSchema(ORJSONModel):
    payment_type: Transaction.PaymentType


class PurchaseResponseSchema(ORJSONModel):
    confirmation_url: Optional[str] = None
