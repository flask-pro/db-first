from typing import Any
from typing import get_args

from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy import Sequence
from sqlalchemy import update
from sqlalchemy.exc import CompileError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from .exceptions import DBALCreateException
from .exceptions import DBALObjectNotFoundException
from .exceptions import DBALUpdateException
from .paginate import PageMixin


class SqlaDBAL[M](PageMixin):
    """Base SqlaDBAL, implement base CRUD sqlalchemy operations."""

    _model: type[M]

    def __init_subclass__(cls) -> None:
        cls._model = get_args(cls.__orig_bases__[0])[0]

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **kwargs) -> M:
        try:
            new_obj = self._model(**kwargs)
        except TypeError as e:
            raise DBALCreateException(repr(e))

        self._session.add(new_obj)

        try:
            self._session.commit()
        except (IntegrityError, ProgrammingError) as e:
            self._session.rollback()
            raise DBALCreateException(repr(e))

        return new_obj

    def bulk_create(self, data: list[dict]) -> Result[Any]:
        try:
            new_objects = self._session.execute(insert(self._model), data)
        except (IntegrityError, ProgrammingError) as e:
            raise DBALCreateException(repr(e))

        return new_objects

    def read(self, id: Any) -> M:
        stmt = select(self._model).where(self._model.id == id)

        try:
            return self._session.scalars(stmt).one()
        except NoResultFound as e:
            raise DBALObjectNotFoundException(repr(e))

    def bulk_read(self, ids: list[Any]) -> Sequence[M]:
        stmt = select(self._model).where(self._model.id.in_(ids))
        return self._session.scalars(stmt).all()

    def read_all(self) -> Sequence[M]:
        stmt = select(self._model)
        return self._session.scalars(stmt).all()

    def update(self, id: Any, **data) -> M:
        stmt = update(self._model).where(self._model.id == id).values(**data).returning(self._model)

        try:
            obj = self._session.scalars(stmt).one()
        except (CompileError, IntegrityError, ProgrammingError) as e:
            raise DBALUpdateException(repr(e))

        return obj

    def bulk_update(self, data: list[dict]) -> None:
        try:
            self._session.execute(update(self._model), data)
        except ProgrammingError as e:
            raise DBALUpdateException(repr(e))
        except StaleDataError as e:
            raise DBALObjectNotFoundException(repr(e))

    def delete(self, id: Any) -> None:
        self._session.execute(delete(self._model).where(self._model.id == id))

    def bulk_delete(self, ids: list[Any]) -> None:
        self._session.execute(delete(self._model).where(self._model.id.in_(ids)))
