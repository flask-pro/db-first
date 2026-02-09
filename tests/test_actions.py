from copy import deepcopy

from db_first import ModelMixin
from db_first.actions import BaseWebAction
from db_first.dbal import SqlaDBAL
from db_first.schemas import BaseSchema
from marshmallow import fields
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from tests.conftest import UNIQUE_STRING


class TestSchema(BaseSchema):
    id = fields.UUID()
    first = fields.String()


def test_actions(fx_db_connection):
    Base, engine, db_session = fx_db_connection

    class TestModel(Base, ModelMixin):
        __tablename__ = 'test_models'

        first: Mapped[str] = mapped_column()

    Base.metadata.create_all(engine)

    class TestModelDBAL(SqlaDBAL[TestModel]):
        """DBAL for TestModel."""

    class CreateTestAction(BaseWebAction):
        def permit(self):
            pass

        def validate(self):
            TestSchema(only=['first']).load(self._data)

        def action(self):
            new_test_obj = TestModelDBAL(self._session).create(**self._data)
            return new_test_obj

        def serialization(self):
            serialized_test_obj = TestSchema().dump(self.result)
            return serialized_test_obj

    data_for_create = {'first': next(UNIQUE_STRING)}
    new_data = CreateTestAction(db_session, data_for_create).run()
    new_data_for_assert = deepcopy(new_data)
    assert new_data_for_assert.pop('id')
    assert new_data_for_assert == data_for_create
