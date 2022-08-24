import enum
import uuid
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy import and_, ForeignKey
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


@declarative_mixin
class MethodsExtensionMixin:
    @classmethod
    async def get(cls, session: AsyncSession, **kwargs):
        filters = [
            getattr(cls, field_name) == field_val
            for field_name, field_val in kwargs.items()
        ]

        stmt = sa.select(cls).where(and_(*filters))
        result = await session.execute(stmt)
        obj = result.scalar()

        if not obj:
            raise ObjectDoesNotExistError

        return obj

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        obj = cls(**kwargs)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)

        return obj

    @classmethod
    async def get_or_create(
        cls, session: AsyncSession, defaults: Optional[dict[str, Any]] = None, **kwargs
    ):
        """
        Gets object for given kwargs, if not found create it with additional kwargs
        from defaults dict.
        """
        if defaults is None:
            defaults = {}

        try:
            return await cls.get(session, **kwargs), False
        except ObjectDoesNotExistError:
            return await cls.create(session, **defaults, **kwargs), True


class Transaction(Base, TimestampMixin, MethodsExtensionMixin):
    __tablename__ = "transactions"
    __table_args__ = (sa.UniqueConstraint("id", "type", name="_id_type_uc"),)

    class TypeEnum(enum.Enum):
        PAYMENT = "PAYMENT"
        REFUND = "REFUND"

    class StatusEnum(enum.Enum):
        # custom
        CREATED = "CREATED"
        FAILED = "FAILED"

        # provided by yookassa
        PENDING = "PENDING"
        WAITING_FOR_CAPTURE = "WAITING_FOR_CAPTURE"
        SUCCEEDED = "SUCCEEDED"
        CANCELED = "CANCELED"

    class PaymentType(enum.Enum):
        CARD = "CARD"
        APAY = "APPLEPAY"
        GPAY = "GOOGLEPAY"
        QR = "QR-CODE"

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
    user_film = relationship(
        "UserFilm", lazy="joined", back_populates="transaction", uselist=False
    )


class Receipt(Base, TimestampMixin, MethodsExtensionMixin):
    __tablename__ = "receipts"

    class StatusEnum(enum.Enum):
        # custom
        CREATED = "CREATED"
        FAILED = "FAILED"

        # provided by yookassa
        PENDING = "PENDING"
        SUCCEEDED = "SUCCEEDED"
        CANCELED = "CANCELED"

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


class ReceiptItem(Base, TimestampMixin, MethodsExtensionMixin):
    __tablename__ = "receipt_items"

    class TypeEnum(enum.Enum):
        FILM = "FILM"
        SUBSCRIPTION = "SUBSCRIPTION"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = sa.Column(
        UUID(as_uuid=True), sa.ForeignKey("receipts.id", ondelete="SET NULL")
    )
    description = sa.Column(sa.String(length=4096), nullable=False)
    quantity = sa.Column(sa.Numeric(14, 3), nullable=False)
    amount = sa.Column(sa.Numeric(14, 3), nullable=False)
    type = sa.Column(sa.Enum(TypeEnum), nullable=False)


class UserFilm(Base, TimestampMixin, MethodsExtensionMixin):
    __tablename__ = "users_films"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(UUID(as_uuid=True), nullable=False)
    film_id = sa.Column(UUID(as_uuid=True), nullable=False)
    watched = sa.Column(sa.Boolean, default=False)
    is_active = sa.Column(sa.Boolean, default=False)
    transaction_id = sa.Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    transaction = relationship("Transaction", back_populates="user_film")

    __table_args__ = (sa.UniqueConstraint("user_id", "film_id", name="_user_film"),)

    @classmethod
    async def update(
        cls, session: AsyncSession, user_id: UUID4, film_id: UUID4, **kwargs
    ) -> "UserFilm":
        user_film = await cls.get(session, user_id=user_id, film_id=film_id)

        for key, value in kwargs.items():
            if key not in ("user_id", "film_id"):
                setattr(user_film, key, value)

        return user_film
