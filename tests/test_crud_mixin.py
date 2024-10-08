from copy import deepcopy
from uuid import UUID

import pytest
from db_first import BaseCRUD
from db_first import ModelMixin
from db_first.mixins.crud import CreateMixin
from db_first.mixins.crud import DeleteMixin
from db_first.mixins.crud import ReadMixin
from db_first.mixins.crud import UpdateMixin
from marshmallow import fields
from marshmallow import Schema
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .conftest import UNIQUE_STRING


def test_crud_mixin(fx_db_connection):
    Base, engine, db_session = fx_db_connection

    class TestModel(Base, ModelMixin):
        __tablename__ = 'test_model'

        first: Mapped[str] = mapped_column()

    Base.metadata.create_all(engine)

    class SchemaOfCreate(Schema):
        first = fields.String()

    class SchemaOfResultCreate(Schema):
        id = fields.UUID()
        first = fields.String()

    class TestCreate(CreateMixin, BaseCRUD):
        class Meta:
            model = TestModel
            session = db_session
            input_schema_of_create = SchemaOfCreate
            output_schema_of_create = SchemaOfResultCreate

    data_for_create = {'first': next(UNIQUE_STRING)}
    TestCreate().create(data=data_for_create, jsonify=True)
    new_data = TestCreate().create(data=data_for_create, jsonify=True)
    new_data_for_assert = deepcopy(new_data)
    assert new_data_for_assert.pop('id')
    assert new_data_for_assert == data_for_create

    class TestRead(ReadMixin, BaseCRUD):
        class Meta:
            model = TestModel
            session = db_session
            output_schema_of_read = SchemaOfResultCreate

    data_for_read = TestRead().read(id=UUID(new_data['id']), jsonify=True)
    assert new_data == data_for_read

    class TestUpdate(UpdateMixin, BaseCRUD):
        class Meta:
            model = TestModel
            session = db_session
            input_schema_of_update = SchemaOfResultCreate
            output_schema_of_update = SchemaOfResultCreate

    data_for_update = {'id': UUID(new_data['id']), 'first': next(UNIQUE_STRING)}
    updated_data = TestUpdate().update(data=data_for_update, jsonify=True)
    data_for_update['id'] = str(data_for_update['id'])
    assert updated_data == data_for_update

    class TestDelete(DeleteMixin, BaseCRUD):
        class Meta:
            model = TestModel
            session = db_session
            input_schema_of_update = SchemaOfResultCreate
            output_schema_of_update = SchemaOfResultCreate

    TestDelete().delete(id=UUID(new_data['id']))

    with pytest.raises(NoResultFound):
        TestRead().read(id=UUID(new_data['id']))
