from typing import Any
from typing import Optional

from sqlalchemy import or_
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase


class QueryMaker:
    """The class builds a SQL query as a SQLAlchemy object.

    The class works only with one table, passed during initialization in the `model` argument.
    If you need to specify parameters for other query tables, then you should pass the parameter
    `statement` containing a pre-prepared request, or write the request directly without using
    `QueryMaker`.

    The request is executed outside of this class
    """

    START_PERIOD_PREFIX = 'start_'
    END_PERIOD_PREFIX = 'end_'

    ASC_SORTING_VALUE = 'asc'
    DESC_SORTING_VALUE = 'desc'

    def __init__(
        self,
        model: DeclarativeBase,
        statement: Optional[Select] = None,
        filter_by: Optional[dict[str, Any]] = None,
        interval_filter_by: Optional[dict[str, Any]] = None,
        search_by: Optional[dict[str, Any]] = None,
        sort_by: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> None:
        self._model = model

        if statement is None:
            self.statement = select(model)
        else:
            self.statement = statement

        self._filter_by = filter_by
        self._interval_filter_by = interval_filter_by
        self._search_by = search_by
        self._sort_by = sort_by
        self._limit = limit
        self._offset = offset

        self._make_statement()

    def _filtration(self) -> None:
        """Adding filtering conditions to the request."""

        for field, value in self._filter_by.items():
            if isinstance(value, list):
                self.statement = self.statement.where(getattr(self._model, field).in_(value))
            else:
                self.statement = self.statement.where(getattr(self._model, field) == value)

    def _interval_filtration(self) -> None:
        """Adding filtering conditions by interval to the query."""

        for field, value in self._interval_filter_by.items():
            if field.startswith(self.START_PERIOD_PREFIX):
                field_name = field.replace(self.START_PERIOD_PREFIX, '', 1)
                self.statement = self.statement.where(getattr(self._model, field_name) >= value)
            elif field.startswith(self.END_PERIOD_PREFIX):
                field_name = field.replace(self.END_PERIOD_PREFIX, '', 1)
                self.statement = self.statement.where(getattr(self._model, field_name) < value)
            else:
                raise ValueError(
                    f'Field <{field}> must contain'
                    f' prefix <{self.START_PERIOD_PREFIX} or <{self.END_PERIOD_PREFIX}>.'
                )

    def _searching(self) -> None:
        """Adding search terms to a query."""

        searching = []
        for field, value in self._search_by.items():
            searching.append(getattr(self._model, field).ilike(f'%{value}%'))

        self.statement = self.statement.where(or_(*searching))

    def _sorting(self) -> None:
        """Adding sorting conditions to a query."""

        for field, value in self._sort_by.items():
            if value == self.ASC_SORTING_VALUE:
                self.statement = self.statement.order_by(getattr(self._model, field))
            elif value == self.DESC_SORTING_VALUE:
                self.statement = self.statement.order_by(getattr(self._model, field).desc())
            else:
                raise ValueError(
                    f'Field <{field}> contain value <{value}>. But must contain'
                    f' value <{self.ASC_SORTING_VALUE}> or <{self.DESC_SORTING_VALUE}>.'
                )

    def _make_statement(self) -> None:
        if self._filter_by:
            self._filtration()

        if self._interval_filter_by:
            self._interval_filtration()

        if self._search_by:
            self._searching()

        if self._sort_by:
            self._sorting()

        if self._limit:
            self.statement = self.statement.limit(self._limit)

        if self._offset:
            self.statement = self.statement.offset(self._offset)
