from typing import Any
from uuid import UUID

import pytest
from db_first import ModelMixin
from db_first.actions import BaseAction
from db_first.actions import BaseWebAction
from db_first.dbal import SqlaDBAL
from db_first.schemas import PaginateActionSchema
from db_first.statement_maker import StatementMaker
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import Select
from sqlalchemy.engine import Result
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

from tests.contrib.schemas import ChildSchema
from tests.contrib.schemas import FatherSchema
from tests.contrib.schemas import ParentPaginationSchema
from tests.contrib.schemas import ParentSchema

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

        _to_dict_schemas = ParentSchema

        first: Mapped[str] = mapped_column()
        second: Mapped[str | None] = mapped_column()

    Base.metadata.create_all(engine)

    return session, Parents, Children, Fathers


@pytest.fixture(scope='session')
def fx_parent_dbal(fx_db):
    session_db, parents_model, _, _ = fx_db

    class ParentsDBAL(SqlaDBAL[parents_model]):
        """DBAL for Parents."""

    return ParentsDBAL


@pytest.fixture(scope='session')
def fx_parent_action__paginate(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    def _create_action(data: dict[str, Any]):
        class PaginateAction(BaseWebAction):
            def permit(self) -> None:
                pass

            def validate(self) -> None:
                PaginateActionSchema().load(self._data)

            def action(self) -> None:
                params = {k: v for k, v in self._data.items() if k not in ['fields']}
                result = fx_parent_dbal(session_db).paginate(**params)
                return result

            def serialization(self) -> None:
                only = self._data.get('fields')
                serialized_result = ParentPaginationSchema(only=only).dump(self.result)
                return serialized_result

        return PaginateAction(session_db, data)

    return _create_action


@pytest.fixture(scope='session')
def fx_parent_action__create(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    def _create_action(data: dict[str, Any]):
        class CreateAction(BaseAction):
            def validate(self) -> None:
                ParentSchema(exclude=['id']).load(self._data)

            def action(self) -> None:
                return fx_parent_dbal(session_db).create(**self._data)

        return CreateAction(session_db, data)

    return _create_action


@pytest.fixture(scope='session')
def fx_parent_action__update(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    def _create_action(data: dict[str, Any]):
        class UpdateAction(BaseAction):
            def validate(self) -> None:
                ParentSchema().load(self._data)

            def action(self) -> None:
                return fx_parent_dbal(session_db).update(**self._data)

        return UpdateAction(session_db, data)

    return _create_action


@pytest.fixture(scope='session')
def fx_child_action__create(fx_db, fx_parent_dbal):
    session_db, _, child_model, _ = fx_db

    class ChildDBAL(SqlaDBAL[child_model]):
        """DBAL for Children."""

    def _create_action(data: dict[str, Any]):
        class CreateAction(BaseAction):
            def validate(self) -> None:
                ChildSchema(exclude=['id']).load(self._data)

            def action(self) -> None:
                return ChildDBAL(session_db).create(**self._data)

        return CreateAction(session_db, data)

    return _create_action


@pytest.fixture(scope='session')
def fx_father_action__create(fx_db, fx_parent_dbal):
    session_db, _, _, father_model = fx_db

    class FathersDBAL(SqlaDBAL[father_model]):
        """DBAL for Fathers."""

    def _create_action(data: dict[str, Any]):
        class CreateAction(BaseAction):
            def validate(self) -> None:
                FatherSchema(exclude=['id']).load(self._data)

            def action(self) -> None:
                return FathersDBAL(session_db).create(**self._data)

        return CreateAction(session_db, data)

    return _create_action


@pytest.fixture
def fx_parents__non_deletion(
    fx_parent_action__create, fx_child_action__create, fx_father_action__create
):
    def _create_item() -> Result:
        new_father = fx_father_action__create({'first': next(UNIQUE_STRING)}).run()

        parent_data = {
            'first': next(UNIQUE_STRING),
            'second': f'full {next(UNIQUE_STRING)}',
            'father_id': new_father.id,
        }
        new_parent = fx_parent_action__create(parent_data).run()
        fx_child_action__create({'first': next(UNIQUE_STRING), 'parent_id': new_parent.id}).run()
        return new_parent

    return _create_item


@pytest.fixture
def fx_make_stmt(fx_db, fx_parents__non_deletion):
    def _create_item(
        model,
        where: dict[str, list[Any]] = None,
        order_by: list[dict[str, list[Any]]] = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select:

        params = {}

        if limit is not None:
            params['limit'] = limit

        if offset is not None:
            params['offset'] = offset

        if where:
            params['where'] = where

        if order_by:
            params['order_by'] = order_by

        statement_maker = StatementMaker(model, **params)
        stmt = statement_maker.make_stmt()

        return stmt

    return _create_item
