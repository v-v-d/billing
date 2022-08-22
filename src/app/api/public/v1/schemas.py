from typing import Optional

from app.api.schemas import ORJSONModel
from app.models import Transaction


class PurchaseRequestSchema(ORJSONModel):
    payment_type: Transaction.PaymentType


class PurchaseResponseSchema(ORJSONModel):
    confirmation_url: Optional[str] = None
