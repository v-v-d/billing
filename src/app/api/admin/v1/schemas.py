import enum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, UUID4

from app.api.internal.v1.schemas import UserFilmOutputSchema
from app.models import Transaction, Receipt, UserFilm


class ReceiptOutputScheme(BaseModel):
    id: UUID4
    ext_id: UUID4
    transaction_id: Optional[UUID4]
    status: Receipt.StatusEnum

    class Config:
        orm_mode = True


class TransactionOutput(BaseModel):
    id: UUID4
    ext_id: UUID4
    user_id: UUID4
    amount: int
    type: Transaction.TypeEnum
    status: Transaction.StatusEnum
    payment_type: Transaction.PaymentType
    created_at: datetime
    updated_at: datetime
    receipt: Optional[ReceiptOutputScheme]
    user_film: Optional[UserFilmOutputSchema]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
