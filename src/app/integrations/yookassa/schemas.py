from enum import Enum
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import AnyHttpUrl

from app.api.schemas import ORJSONModel


class StatusEnum(str, Enum):
    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class ResponseConfirmationSchema(ORJSONModel):
    confirmation_url: AnyHttpUrl


class YookassaPaymentResponseSchema(ORJSONModel):
    id: UUID
    status: StatusEnum
    confirmation: ResponseConfirmationSchema


class CancellationDetailsSchema(ORJSONModel):
    reason: str


class YookassaRefundResponseSchema(ORJSONModel):
    id: UUID
    status: StatusEnum
    cancellation_details: Optional[CancellationDetailsSchema]
