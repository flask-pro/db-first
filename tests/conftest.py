from typing import Optional
from uuid import UUID

import pytest
from db_first import BaseCRUD
from db_first import ModelMixin
from db_first.mixins import PaginationMixin
from db_first.mixins.crud import CreateMixin
from db_first.mixins.crud import DeleteMixin
from db_first.mixins.crud import ReadMixin
from db_first.mixins.crud import UpdateMixin
from marshmallow import fields
from marshmallow import Schema
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.engine import Result
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

UNIQUE_STRING = (f'name_{number}' for number in range(1_000))


@pytest.fixture(scope='session')
def fx_db_connection():
    engine = create_engine('sqlite://', echo=True, future=True)
    session = Session(engine)
    Base = declarative_base()
    return Base, engine, session


@pytest.fixture(scope='session')
def fx_db(fx_db_connection):
    Base, engine, session = fx_db_connection

    class Parents(Base, ModelMixin):
        __tablename__ = 'parents'

        first: Mapped[str] = mapped_column()
        second: Mapped[Optional[str]] = mapped_column()
        father_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('fathers.id'))

        father = relationship(
            'Fathers', backref='parents', cascade='all, delete-orphan', single_parent=True
        )

        @hybrid_property
        def child_count(self) -> int:
            return len(self.children)

    class Children(Base, ModelMixin):
        __tablename__ = 'children'

        first: Mapped[str] = mapped_column()
        second: Mapped[Optional[str]] = mapped_column()
        parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('parents.id'))

        parent = relationship(
            'Parents', backref='children', cascade='all, delete-orphan', single_parent=True
        )

    class Fathers(Base, ModelMixin):
        __tablename__ = 'fathers'

        first: Mapped[str] = mapped_column()
        second: Mapped[Optional[str]] = mapped_column()

    Base.metadata.create_all(engine)

    return session, Parents, Children, Fathers


@pytest.fixture(scope='session')
def fx_father_schema_of_create() -> type[Schema]:
    class SchemaOfCreate(Schema):
        first = fields.String(required=True)
        second = fields.String()

    return SchemaOfCreate


@pytest.fixture(scope='session')
def fx_father_output_schema(fx_father_schema_of_create) -> type[Schema]:
    class OutputSchema(fx_father_schema_of_create):
        id = fields.String(required=True)
        created_at = fields.DateTime()

    return OutputSchema


@pytest.fixture(scope='session')
def fx_parent_schema_of_create() -> type[Schema]:
    class SchemaOfCreate(Schema):
        first = fields.String(required=True)
        second = fields.String()
        father_id = fields.UUID()

    return SchemaOfCreate


@pytest.fixture(scope='session')
def fx_parent_schema_of_update(fx_parent_schema_of_create) -> type[Schema]:
    class SchemaOfUpdate(fx_parent_schema_of_create):
        id = fields.UUID(required=True)

    return SchemaOfUpdate


@pytest.fixture(scope='session')
def fx_parent_output_schema(fx_father_output_schema, fx_child_output_schema) -> type[Schema]:
    class OutputSchema(Schema):
        id = fields.String(required=True)
        first = fields.String(required=True)
        second = fields.String()
        created_at = fields.DateTime()
        father = fields.Nested(fx_father_output_schema)
        children = fields.Nested(fx_child_output_schema, many=True)

    return OutputSchema


@pytest.fixture(scope='session')
def fx_parent_paginate_schema(fx_parent_output_schema) -> type[Schema]:
    class PaginateSchema(fx_parent_output_schema):
        pass

    return PaginateSchema


@pytest.fixture(scope='session')
def fx_child_schema_of_create() -> type[Schema]:
    class SchemaOfCreate(Schema):
        first = fields.String(required=True)
        second = fields.String()
        parent_id = fields.UUID()

    return SchemaOfCreate


@pytest.fixture(scope='session')
def fx_child_output_schema(fx_child_schema_of_create) -> type[Schema]:
    class SchemaOfCreate(fx_child_schema_of_create):
        id = fields.String(required=True)

    return SchemaOfCreate


@pytest.fixture(scope='session')
def fx_parent_controller(
    fx_db, fx_parent_schema_of_create, fx_parent_schema_of_update, fx_parent_paginate_schema
):
    session_db, parents_model, _, _ = fx_db

    class Parent(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, PaginationMixin, BaseCRUD):
        class Meta:
            session = session_db
            model = parents_model
            input_schema_of_create = fx_parent_schema_of_create
            input_schema_of_update = fx_parent_schema_of_update
            filterable = ['id', 'first']
            interval_filterable = ['created_at']
            sortable = ['created_at']
            searchable = ['first']
            schema_of_paginate = fx_parent_paginate_schema

    return Parent()


@pytest.fixture(scope='session')
def fx_child_controller(fx_db, fx_child_schema_of_create):
    session_db, _, child_model, _ = fx_db

    class Child(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, PaginationMixin, BaseCRUD):
        class Meta:
            session = session_db
            model = child_model
            input_schema_of_create = fx_child_schema_of_create
            filterable = ['id', 'parent_id']
            sortable = ['parent_id', 'created_at']

    return Child()


@pytest.fixture(scope='session')
def fx_father_controller(fx_db, fx_father_schema_of_create):
    session_db, _, _, father_model = fx_db

    class Father(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, PaginationMixin, BaseCRUD):
        class Meta:
            session = session_db
            model = father_model
            input_schema_of_create = fx_father_schema_of_create

    return Father()


@pytest.fixture
def fx_parents__non_deletion(fx_parent_controller, fx_child_controller, fx_father_controller):
    def _create_item() -> Result:
        new_father = fx_father_controller.create(data={'first': next(UNIQUE_STRING)})
        new_parent = fx_parent_controller.create(
            data={
                'first': next(UNIQUE_STRING),
                'second': f'full {next(UNIQUE_STRING)}',
                'father_id': new_father.id,
            }
        )
        fx_child_controller.create(data={'first': next(UNIQUE_STRING), 'parent_id': new_parent.id})
        return new_parent

    return _create_item
