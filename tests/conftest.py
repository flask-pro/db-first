from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.engine import Result
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

from .contrib.schemas import ChildSchema
from .contrib.schemas import FatherSchema
from .contrib.schemas import ParentSchema
from .contrib.schemas import ParentSchemaOfPaginate
from .contrib.schemas import ParentSchemaParametersOfPaginate
from src.db_first import BaseCRUD
from src.db_first import ModelMixin
from src.db_first.decorators import Validation
from src.db_first.mixins.crud import CreateMixin
from src.db_first.mixins.crud import DeleteMixin
from src.db_first.mixins.crud import ReadMixin
from src.db_first.mixins.crud import UpdateMixin

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
        second: Mapped[str | None] = mapped_column()
        father_id: Mapped[UUID | None] = mapped_column(ForeignKey('fathers.id'))

        father = relationship(
            'Fathers', backref='parents', cascade='all, delete-orphan', single_parent=True
        )

        @hybrid_property
        def child_count(self) -> int:
            return len(self.children)

    class Children(Base, ModelMixin):
        __tablename__ = 'children'

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()
        parent_id: Mapped[UUID | None] = mapped_column(ForeignKey('parents.id'))

        parent = relationship(
            'Parents', backref='children', cascade='all, delete-orphan', single_parent=True
        )

    class Fathers(Base, ModelMixin):
        __tablename__ = 'fathers'

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()

    Base.metadata.create_all(engine)

    return session, Parents, Children, Fathers


@pytest.fixture(scope='session')
def fx_parent_controller(fx_db):
    session_db, parents_model, _, _ = fx_db

    class Parent(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
        class Meta:
            session = session_db
            model = parents_model
            filterable = ['id', 'first']
            interval_filterable = ['created_at']
            sortable = ['created_at']
            searchable = ['first']

        @Validation.input(ParentSchema, keys=('first', 'second', 'father_id'))
        @Validation.output(ParentSchema)
        def create(self, **data: dict) -> Result or dict:
            return super().create_object(**data)

        @Validation.input(ParentSchema, keys=('id', 'first', 'second', 'father_id'))
        @Validation.output(ParentSchema)
        def update(self, **data: dict) -> Result or dict:
            return super().update_object(**data)

        @Validation.input(ParentSchemaParametersOfPaginate)
        @Validation.output(ParentSchemaOfPaginate, serialize=True)
        def paginate(self, **data: dict) -> Result or dict:
            if 'ids' in data:
                data['id'] = data.pop('ids')
            return super().base_paginate(**data)

        @Validation.input(ParentSchemaParametersOfPaginate)
        @Validation.output(ParentSchemaOfPaginate, keys=('items.id',), serialize=True)
        def paginate_ids(self, **data: dict) -> Result or dict:
            if 'ids' in data:
                data['id'] = data.pop('ids')
            return super().base_paginate(**data)

    return Parent()


@pytest.fixture(scope='session')
def fx_child_controller(fx_db):
    session_db, _, child_model, _ = fx_db

    class Child(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
        class Meta:
            session = session_db
            model = child_model
            filterable = ['id', 'parent_id']
            sortable = ['parent_id', 'created_at']

        @Validation.input(ChildSchema, keys=('first', 'second', 'parent_id'))
        @Validation.output(ChildSchema)
        def create(self, **data: dict) -> Result or dict:
            return super().create_object(**data)

    return Child()


@pytest.fixture(scope='session')
def fx_father_controller(fx_db):
    session_db, _, _, father_model = fx_db

    class Father(CreateMixin, ReadMixin, UpdateMixin, DeleteMixin, BaseCRUD):
        class Meta:
            session = session_db
            model = father_model

        @Validation.input(FatherSchema, keys=('first', 'second'))
        @Validation.output(FatherSchema)
        def create(self, **data: dict) -> Result or dict:
            return super().create_object(**data)

    return Father()


@pytest.fixture
def fx_parents__non_deletion(fx_parent_controller, fx_child_controller, fx_father_controller):
    def _create_item() -> Result:
        new_father = fx_father_controller.create(first=next(UNIQUE_STRING))
        new_parent = fx_parent_controller.create(
            first=next(UNIQUE_STRING), second=f'full {next(UNIQUE_STRING)}', father_id=new_father.id
        )
        fx_child_controller.create(first=next(UNIQUE_STRING), parent_id=new_parent.id)
        return new_parent

    return _create_item
