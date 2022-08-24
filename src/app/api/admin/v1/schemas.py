import enum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, UUID4

from app.models import Transaction, Receipt, UserFilm


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
    receipts: Optional[List[Receipt]]
    user_film: Optional[UserFilm]

    class Config:
        orm_mode = True
