from pydantic import BaseModel, UUID4


class PaymentObjectSchema(BaseModel):
    id: UUID4
    status: str
    paid: bool


class PaymentNotificationSchema(BaseModel):
    type: str
    event: str
    object: PaymentObjectSchema
