from typing import Any

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.engine import Result


class CreateMixin:
    """Create object in database.

    This mixin supports the following options in the Meta class:
    ```
    class CustomController(CreateMixin, BaseCRUD):
        class Meta:
            session = Session
            model = Model
            input_schema_of_create = InputSchema
            output_schema_of_create = OutputSchema

    custom_controller = CustomController()
    ```

    `input_schema_of_create` - marshmallow schema for validating and deserialization input data.
    `output_schema_of_create` - marshmallow schema for serialization output data.
    """

    def create_object(self, **data) -> Result:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        new_obj = model(**data)
        session.add(new_obj)
        session.commit()
        return new_obj

    def create(self, data: dict, serialize: bool = False) -> Result or dict:
        deserialized_data = self.deserialize_data('input_schema_of_create', data)
        new_object = self.create_object(**deserialized_data)

        if serialize:
            return self.serialize_data('output_schema_of_create', new_object)

        return new_object


class ReadMixin:
    """Read object from database."""

    def get_object(self, id: Any) -> Result:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')
        return session.scalars(select(model).where(model.id == id)).one()

    def read(self, id, serialize: bool = False) -> Result or dict:
        obj = self.get_object(id)

        if serialize:
            return self.serialize_data('output_schema_of_read', obj)

        return obj


class UpdateMixin:
    """Update object in database."""

    def update_object(self, id: Any, **data) -> Result:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        stmt = update(model).where(model.id == id).values(**data)
        session.execute(stmt)

        obj = session.scalars(select(model).where(model.id == id)).one()
        return obj

    def update(self, data: dict, serialize: bool = False) -> Result or dict:
        deserialized_data = self.deserialize_data('input_schema_of_update', data)
        updated_object = self.update_object(**deserialized_data)

        if serialize:
            return self.serialize_data('output_schema_of_update', updated_object)

        return updated_object


class DeleteMixin:
    """Delete object from database."""

    def delete_object(self, id: Any) -> None:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        session.execute(delete(model).where(model.id == id))

    def delete(self, id: Any) -> None:
        self.delete_object(id)
