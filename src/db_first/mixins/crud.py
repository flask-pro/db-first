from typing import Any

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.engine import Result


class CreateMixin:
    """Create object in database."""

    def _create_object(self, **data) -> Result:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        new_obj = model(**data)
        session.add(new_obj)
        session.commit()
        return new_obj

    def create(self, data: dict, validating: bool = True, jsonify: bool = False) -> Result or dict:
        if validating:
            self._deserialize_data('input_schema_of_create', data)

        new_object = self._create_object(**data)

        if jsonify:
            return self._data_to_json('output_schema_of_create', new_object)

        return new_object


class ReadMixin:
    """Read object from database."""

    def _read_object(self, id: Any) -> Result:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')
        return session.scalars(select(model).where(model.id == id)).one()

    def read(self, id, jsonify: bool = False) -> Result or dict:
        obj = self._read_object(id)

        if jsonify:
            return self._data_to_json('output_schema_of_read', obj)

        return obj


class UpdateMixin:
    """Update object in database."""

    def _update_object(self, id: Any, **data) -> Result:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        obj = session.scalars(select(model).where(model.id == id)).one()
        for k, v in data.items():
            setattr(obj, k, v)
        session.commit()
        return obj

    def update(self, data: dict, validating: bool = True, jsonify: bool = False) -> Result or dict:
        if validating:
            self._deserialize_data('input_schema_of_update', data)

        updated_object = self._update_object(**data)

        if jsonify:
            return self._data_to_json('output_schema_of_update', updated_object)

        return updated_object


class DeleteMixin:
    """Delete object from database."""

    def _delete_object(self, id: Any) -> None:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        session.execute(delete(model).where(model.id == id))
        session.commit()

    def delete(self, id: Any) -> None:
        self._delete_object(id)
