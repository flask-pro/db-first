import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


def make_uuid4() -> UUID:
    return uuid.uuid4()


class ModelMixin:
    """Mixin for table model."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=make_uuid4, comment='UUID')
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, comment='Date and time created'
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        onupdate=datetime.utcnow, comment='Date and time updated'
    )
