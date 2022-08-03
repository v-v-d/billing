import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin

from app.database import Base


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


class Example(Base, TimestampMixin):
    __tablename__ = "examples"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
