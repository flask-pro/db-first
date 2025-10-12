from uuid import uuid4

from marshmallow import fields
from marshmallow import Schema
from sqlalchemy import Result
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.db_first import BaseCRUD
from src.db_first import ModelMixin
from src.db_first.decorators import Validation
from src.db_first.mixins.crud import CreateMixin
from src.db_first.mixins.crud import DeleteMixin
from src.db_first.mixins.crud import ReadMixin
from src.db_first.mixins.crud import UpdateMixin
from tests.conftest import UNIQUE_STRING


class TestSchema(Schema):
    id = fields.UUID()
    first = fields.String()


class BulkTestSchema(Schema):
    items = fields.Nested(TestSchema, many=True)


class BulkReadTestSchema(Schema):
    items = fields.List(fields.UUID())


def test_crud_mixin__bulk(fx_db_connection):
    Base, engine, db_session = fx_db_connection

    class TestModel(Base, ModelMixin):
        __tablename__ = 'test_model__bulk'

        first: Mapped[str] = mapped_column()

    Base.metadata.create_all(engine)

    class TestCRUD(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
        class Meta:
            model = TestModel
            session = db_session
            filterable = ['id']

        @Validation.input(BulkTestSchema)
        def create(self, **data) -> None:
            super().bulk_create_object(data['items'])

        @Validation.input(BulkReadTestSchema)
        @Validation.output(BulkTestSchema, serialize=True)
        def read(self, **data) -> dict[str, list[Result]]:
            return {'items': super().bulk_read_object(data['items'])}

        @Validation.input(BulkTestSchema)
        @Validation.output(BulkTestSchema, serialize=True)
        def update(self, **data) -> None:
            return super().bulk_update_object(data['items'])

        @Validation.input(BulkReadTestSchema)
        def delete(self, **data) -> None:
            super().bulk_delete_object(data['items'])

    id_ = str(uuid4())
    data_for_create = {'items': [{'id': id_, 'first': next(UNIQUE_STRING)}]}
    TestCRUD().create(**data_for_create)

    data_for_read = TestCRUD().read(**{'items': [id_]})
    assert data_for_create == data_for_read

    data_for_update = {'items': [{'id': id_, 'first': next(UNIQUE_STRING)}]}
    TestCRUD().update(**data_for_update)
    updated_data = TestCRUD().read(**{'items': [id_]})
    assert updated_data == data_for_update

    TestCRUD().delete(**{'items': [id_]})
    assert not TestCRUD().read(**{'items': [id_]})['items']
