import uuid
from datetime import datetime
from datetime import timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import validates


def make_uuid4() -> uuid.UUID:
    return uuid.uuid4()


def make_datetime_with_utc() -> datetime:
    return datetime.now(timezone.utc)


class ModelMixin:
    """Mixin for table model."""

    EMPTY_VALUES: tuple[None, list, dict, tuple] = (None, [], {}, ())

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=make_uuid4, comment='UUID')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=make_datetime_with_utc, comment='Date and time created'
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=make_datetime_with_utc, comment='Date and time updated'
    )

    @staticmethod
    def validate_utc_timezone(key: str, value: datetime or None) -> datetime:
        time_zone = getattr(value, 'tzinfo', None)
        if time_zone != timezone.utc:
            raise ValueError(
                f'Field <{key}> must be datetime with UTC timezone,'
                f' but received timezone: <{time_zone}>'
            )

        return value

    @validates('created_at', 'updated_at')
    def validate_timezone(self, key, value) -> datetime:
        return self.validate_utc_timezone(key, value)

    def to_dict(self, fields: dict[str, dict or list or Ellipsis]):
        data = {}
        for field, value in fields.items():
            value_from_db = None

            if value is Ellipsis:
                value_from_db = getattr(self, field)

            elif isinstance(value, dict):
                obj = getattr(self, field)
                if obj:
                    value_from_db = obj.to_dict(value)

            elif isinstance(value, list):
                value_from_db = []
                for obj in getattr(self, field):
                    for item in value:
                        dictable_value_from_db = obj.to_dict(item)
                        if dictable_value_from_db not in self.EMPTY_VALUES:
                            value_from_db.append(dictable_value_from_db)

            else:
                value_from_db = self.to_dict(value)

            if value_from_db not in self.EMPTY_VALUES:
                data[field] = value_from_db

        return data
