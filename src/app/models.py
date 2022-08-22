import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_mixin, relationship

from app.database import Base


class ObjectDoesNotExistError(Exception):
    """Raise it if object does not exist in database."""


@declarative_mixin
class TimestampMixin:
    created_at = sa.Column(
        sa.DateTime(timezone=False), default=lambda: datetime.utcnow()
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=False),
        default=lambda: datetime.utcnow(),
        onupdate=datetime.utcnow,
    )


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (sa.UniqueConstraint("id", "type", name="_id_type_uc"),)

    class TypeEnum(enum.Enum):
        PAYMENT = "payment"
        REFUND = "refund"

    class StatusEnum(enum.Enum):
        # custom
        CREATED = "created"
        FAILED = "failed"

        # provided by yookassa
        PENDING = "pending"
        WAITING_FOR_CAPTURE = "waiting_for_capture"
        SUCCEEDED = "succeeded"
        CANCELED = "canceled"

    class PaymentType(enum.Enum):
        CARD = "card"
        APAY = "applepay"
        GPAY = "googlepay"
        QR = "QR-code"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ext_id = sa.Column(UUID(as_uuid=True), unique=True)
    user_id = sa.Column(UUID(as_uuid=True), nullable=False, index=True)
    amount = sa.Column(
        sa.Numeric(14, 3), sa.CheckConstraint("amount>0"), nullable=False
    )
    type = sa.Column(sa.Enum(TypeEnum), nullable=False, index=True)
    status = sa.Column(
        sa.Enum(StatusEnum), default=StatusEnum.CREATED.value, index=True
    )
    payment_type = sa.Column(sa.Enum(PaymentType), nullable=False, index=True)

    receipts = relationship("Receipt", lazy="joined", back_populates="transactions")


class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"

    class StatusEnum(enum.Enum):
        # custom
        CREATED = "created"
        FAILED = "failed"

        # provided by yookassa
        PENDING = "pending"
        SUCCEEDED = "succeeded"
        CANCELED = "canceled"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ext_id = sa.Column(UUID(as_uuid=True), index=True)
    transaction_id = sa.Column(
        UUID(as_uuid=True), sa.ForeignKey("transactions.id", ondelete="SET NULL")
    )
    status = sa.Column(
        sa.Enum(StatusEnum), default=StatusEnum.CREATED.value, index=True
    )

    transactions = relationship("Transaction", lazy="joined", back_populates="receipts")
    items = relationship("ReceiptItem", lazy="joined")


class ReceiptItem(Base, TimestampMixin):
    __tablename__ = "receipt_items"

    class TypeEnum(enum.Enum):
        FILM = "film"
        SUBSCRIPTION = "subscription"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = sa.Column(
        UUID(as_uuid=True), sa.ForeignKey("receipts.id", ondelete="SET NULL")
    )
    description = sa.Column(sa.String(length=4096), nullable=False)
    quantity = sa.Column(sa.Numeric(14, 3), nullable=False)
    amount = sa.Column(sa.Numeric(14, 3), nullable=False)
    type = sa.Column(sa.Enum(TypeEnum), nullable=False)


class UserFilm(Base, TimestampMixin):
    __tablename__ = "users_films"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(UUID(as_uuid=True), nullable=False)
    film_id = sa.Column(UUID(as_uuid=True), nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    watched = sa.Column(sa.Boolean, default=False)
    is_active = sa.Column(sa.Boolean, default=True)

    __table_args__ = (sa.UniqueConstraint("user_id", "film_id", name="_user_film"),)

    @classmethod
    async def update(
        cls, session: AsyncSession, user_id: UUID4, film_id: UUID4, **kwargs
    ):
        user_film = await cls.get(session, user_id, film_id)

        for key, value in kwargs.items():
            if key not in ("user_id", "film_id"):
                setattr(user_film, key, value)

        return user_film

    @classmethod
    async def get(cls, session: AsyncSession, user_id: UUID4, film_id: UUID4):
        stmt = sa.select(UserFilm).where(
            and_(UserFilm.user_id == user_id, UserFilm.film_id == film_id)
        )
        result = await session.execute(stmt)
        user_film = result.scalar()

        if not user_film:
            raise ObjectDoesNotExistError

        return user_film
