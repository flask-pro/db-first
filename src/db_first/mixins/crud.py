from math import ceil
from typing import Any

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session

from ..statement_maker import StatementMaker


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

    def create_object(self, **kwargs) -> Result:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        new_obj = model(**kwargs)
        session.add(new_obj)
        session.commit()
        return new_obj

    def bulk_create_object(self, data: list[dict]) -> None:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        session.execute(insert(model), data)


class ReadMixin:
    """Read objects from database.

    Mixin with get paginated result.

    This mixin supports the following options in the Meta class:
    ```
    class CustomController(PaginationMixin, BaseCRUD):
        class Meta:
            session = Session
            model = Model
            filterable = ['id']
            interval_filterable = ['id']
            sortable = ['id']
            searchable = ['id']
            schema_of_paginate = Schema

    custom_controller = CustomController()
    ```
    Required options:
    `session` - session object for connect to database.
    `model` - sqlalchemy model.
    `input_schema_of_read` - marshmallow schema for validating and deserialization input data.
    `output_schema_of_read` - marshmallow schema for serialization output data.

    Optional options:
    `per_page` - items per page (default = 20).
    `max_per_page` - maximum items per page (default = 100).
    `filterable` - list of fields allowed for filtration.
    `interval_filterable` - list of fields allowed for filtration interval.
    `sortable` - list of fields allowed for sorting.
    `searchable` - a list of fields allowed for search for by substring.
    """

    def _calculate_items_per_page(
        self, session: Session, statement: Select, per_page: int
    ) -> tuple[int, int]:
        total = session.execute(
            statement.with_only_columns(func.count(self.Meta.model.id)).order_by(None)
        ).scalar_one()

        if per_page == 0:
            pages = 0
        else:
            pages = ceil(total / per_page)

        return pages, total

    def _make_metadata(self, session: Session, page, per_page, statement):
        pages, total = self._calculate_items_per_page(session, statement, per_page)
        return {'pagination': {'page': page, 'per_page': per_page, 'pages': pages, 'total': total}}

    def _paginate(
        self,
        statement: Select | None,
        page: int = 1,
        per_page: int | None = 20,
        max_per_page: int | None = 100,
        include_metadata: bool = False,
    ) -> dict:
        session: Session = self._get_option_from_meta('session')

        if per_page > max_per_page:
            per_page = max_per_page
        elif per_page < 0:
            per_page = 0

        if page < 1:
            page = 1

        items = {'items': []}
        if include_metadata:
            items['_metadata'] = self._make_metadata(session, page, per_page, statement)

        if per_page != 0:
            statement = statement.limit(per_page).offset((page - 1) * per_page)
            paginated_rows = session.scalars(statement).all()
        else:
            paginated_rows = []

        items['items'] = paginated_rows

        return items

    def base_paginate(
        self,
        page: int = 1,
        per_page: int | None = None,
        max_per_page: int | None = None,
        statement: Select | None = None,
        include_metadata: bool = False,
        **kwargs,
    ) -> Result or dict:
        model = self._get_option_from_meta('model')

        filterable_fields = self._get_option_from_meta('filterable', ())
        interval_filterable_fields = self._get_option_from_meta('interval_filterable', ())
        searchable_fields = self._get_option_from_meta('searchable', ())
        sortable_fields = self._get_option_from_meta('sortable', ())

        stmt = StatementMaker(
            model,
            kwargs,
            statement=statement,
            filterable_fields=filterable_fields,
            interval_filterable_fields=interval_filterable_fields,
            searchable_fields=searchable_fields,
            sortable_fields=sortable_fields,
        ).make_statement()

        if per_page is None:
            per_page = self._get_option_from_meta('per_page', 20)

        if max_per_page is None:
            max_per_page = self._get_option_from_meta('max_per_page', 100)

        items = self._paginate(
            statement=stmt,
            page=page,
            per_page=per_page,
            max_per_page=max_per_page,
            include_metadata=include_metadata,
        )

        return items

    def read_object(self, id: Any) -> Result:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        stmt = select(model).where(model.id == id)
        return session.scalars(stmt).one()

    def bulk_read_object(self, ids: list[Any]) -> list[Result]:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        stmt = select(model).where(model.id.in_(ids))
        return session.scalars(stmt).all()


class UpdateMixin:
    """Update object in database.

    This mixin supports the following options in the Meta class:
    ```
    class CustomController(CreateMixin, BaseCRUD):
        class Meta:
            session = Session
            model = Model
            input_schema_of_update = InputSchema
            output_schema_of_update = OutputSchema

    custom_controller = CustomController()
    ```

    `input_schema_of_update` - marshmallow schema for validating and deserialization input data.
    `output_schema_of_update` - marshmallow schema for serialization output data.
    """

    def update_object(self, id: Any, **kwargs) -> Result:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        stmt = update(model).where(model.id == id).values(**kwargs).returning(model)
        obj = session.scalars(stmt).one()
        return obj

    def bulk_update_object(self, data: list[dict]) -> None:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        session.execute(update(model), data)


class DeleteMixin:
    """Delete object from database."""

    def delete_object(self, id: Any) -> None:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        session.execute(delete(model).where(model.id == id))

    def bulk_delete_object(self, data: list[Any]) -> None:
        """If this method does not suit you, simply override it in your class."""

        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        session.execute(delete(model).where(model.id.in_(data)))
