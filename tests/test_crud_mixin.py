from copy import deepcopy
from uuid import UUID
from uuid import uuid4

import pytest
from marshmallow import fields
from sqlalchemy import Result
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.db_first import BaseCRUD
from src.db_first import ModelMixin
from src.db_first.decorators import Validation
from src.db_first.exc import MetaNotFound
from src.db_first.exc import OptionNotFound
from src.db_first.mixins.crud import CreateMixin
from src.db_first.mixins.crud import DeleteMixin
from src.db_first.mixins.crud import ReadMixin
from src.db_first.mixins.crud import UpdateMixin
from src.db_first.schemas import BaseSchema
from tests.conftest import UNIQUE_STRING


class TestSchema(BaseSchema):
    id = fields.UUID()
    first = fields.String()


def test_crud_mixin(fx_db_connection):
    Base, engine, db_session = fx_db_connection

    class TestModel(Base, ModelMixin):
        __tablename__ = 'test_model'

        first: Mapped[str] = mapped_column()

    Base.metadata.create_all(engine)

    class TestCRUD(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
        class Meta:
            model = TestModel
            session = db_session
            filterable = ['id']

        @Validation.input(TestSchema)
        @Validation.output(TestSchema, serialize=True)
        def create(self, **data) -> Result:
            return super().create_object(**data)

        @Validation.input(TestSchema, keys=['id'])
        @Validation.output(TestSchema, serialize=True)
        def read(self, **data) -> Result:
            return super().read_object(data['id'])

        @Validation.input(TestSchema)
        @Validation.output(TestSchema, serialize=True)
        def update(self, **data) -> Result:
            return super().update_object(**data)

        @Validation.input(TestSchema, keys=['id'])
        def delete(self, **data) -> None:
            super().delete_object(**data)

    data_for_create = {'first': next(UNIQUE_STRING)}
    TestCRUD().create(**data_for_create)
    new_data = TestCRUD().create(**data_for_create)
    new_data_for_assert = deepcopy(new_data)
    assert new_data_for_assert.pop('id')
    assert new_data_for_assert == data_for_create

    data_for_read = TestCRUD().read(**{'id': UUID(new_data['id'])})
    assert new_data == data_for_read

    data_for_update = {'id': UUID(new_data['id']), 'first': next(UNIQUE_STRING)}
    updated_data = TestCRUD().update(**data_for_update)
    data_for_update['id'] = str(data_for_update['id'])
    assert updated_data == data_for_update

    TestCRUD().delete(**{'id': UUID(new_data['id'])})

    with pytest.raises(NoResultFound):
        assert not TestCRUD().read(**{'id': UUID(new_data['id'])})


def test_crud_mixin__wrong_meta(fx_db_connection):

    class TestController(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
        pass

    data_for_create = {'first': next(UNIQUE_STRING)}
    with pytest.raises(MetaNotFound) as e:
        TestController().create_object(**data_for_create)
    assert e.value.args[0] == 'You need add class Meta with options.'

    with pytest.raises(MetaNotFound) as e:
        TestController().read_object(**{'id': uuid4()})
    assert e.value.args[0] == 'You need add class Meta with options.'

    data_for_update = {'id': uuid4(), 'first': next(UNIQUE_STRING)}
    with pytest.raises(MetaNotFound) as e:
        TestController().update_object(**data_for_update)
    assert e.value.args[0] == 'You need add class Meta with options.'

    with pytest.raises(MetaNotFound) as e:
        TestController().delete_object(**{'id': uuid4()})
    assert e.value.args[0] == 'You need add class Meta with options.'


def test_crud_mixin__wrong_options_in_meta(fx_db_connection):

    class TestController(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
        class Meta:
            pass

    data_for_create = {'first': next(UNIQUE_STRING)}
    with pytest.raises(OptionNotFound) as e:
        TestController().create_object(**data_for_create)
    assert e.value.args[0] == 'Option <session> not set in Meta class.'

    with pytest.raises(OptionNotFound) as e:
        TestController().read_object(**{'id': uuid4()})
    assert e.value.args[0] == 'Option <session> not set in Meta class.'

    data_for_update = {'id': uuid4(), 'first': next(UNIQUE_STRING)}
    with pytest.raises(OptionNotFound) as e:
        TestController().update_object(**data_for_update)
    assert e.value.args[0] == 'Option <session> not set in Meta class.'

    with pytest.raises(OptionNotFound) as e:
        TestController().delete_object(**{'id': uuid4()})
    assert e.value.args[0] == 'Option <session> not set in Meta class.'
