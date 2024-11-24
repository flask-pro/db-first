from collections.abc import Iterable
from typing import Any
from typing import Optional

from sqlalchemy import or_
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase


class StatementMaker:
    """The class builds a SQL statement as a SQLAlchemy object.

    The class works only with one table, passed during initialization in the `model` argument.
    If you need to specify parameters for other query tables, then you should pass the parameter
    `statement` containing a pre-prepared request, or write the request directly without using
    `QueryMaker`.

    The request is executed outside of this class
    """

    START_PERIOD_PREFIX = 'start_'
    END_PERIOD_PREFIX = 'end_'

    SEARCH_PREFIX = 'search_'

    SORT_PREFIX = 'sort_'
    ASC_SORTING_VALUE = 'asc'
    DESC_SORTING_VALUE = 'desc'

    def __init__(
        self,
        model: DeclarativeBase,
        data: dict[str, Any],
        statement: Optional[Select] = None,
        filterable_fields: Iterable = (),
        interval_filterable_fields: Iterable = (),
        searchable_fields: Iterable = (),
        sortable_fields: Iterable = (),
    ) -> None:
        self._model = model
        self._data = data

        if statement is None:
            self.stmt = select(model)
        else:
            self.stmt = statement

        self._filterable_fields = filterable_fields
        self._interval_filterable_fields = interval_filterable_fields
        self._searchable_fields = searchable_fields
        self._sortable_fields = sortable_fields

    def _add_filtration(self) -> None:
        """Adding filtering conditions to the statement."""

        for field in self._filterable_fields:
            if field not in self._data:
                continue

            if isinstance(self._data[field], list):
                self.stmt = self.stmt.where(getattr(self._model, field).in_(self._data[field]))
            else:
                self.stmt = self.stmt.where(getattr(self._model, field) == self._data[field])

    def _add_interval_filtration(self) -> None:
        """Adding filtering conditions by interval to the statement."""

        for field in self._interval_filterable_fields:
            start_field_name = f'{self.START_PERIOD_PREFIX}{field}'
            if start_field_name in self._data:
                self.stmt = self.stmt.where(
                    getattr(self._model, field) >= self._data[start_field_name]
                )

            end_field_name = f'{self.END_PERIOD_PREFIX}{field}'
            if end_field_name in self._data:
                self.stmt = self.stmt.where(
                    getattr(self._model, field) < self._data[end_field_name]
                )

    def _add_searching(self) -> None:
        """Adding search terms to a statement."""

        searching = []
        for field in self._searchable_fields:
            search_field_name = f'{self.SEARCH_PREFIX}{field}'
            if search_field_name in self._data:
                searching.append(
                    getattr(self._model, field).ilike(f'%{self._data[search_field_name]}%')
                )
        if searching:
            self.stmt = self.stmt.where(or_(*searching))

    def _add_sorting(self) -> None:
        """Adding sorting conditions to a statement."""

        for field in self._sortable_fields:
            sort_field_name = f'{self.SORT_PREFIX}{field}'
            if sort_field_name not in self._data:
                continue

            if self._data[sort_field_name] == self.ASC_SORTING_VALUE:
                self.stmt = self.stmt.order_by(getattr(self._model, field))
            elif self._data[sort_field_name] == self.DESC_SORTING_VALUE:
                self.stmt = self.stmt.order_by(getattr(self._model, field).desc())
            else:
                raise ValueError(
                    f'Field <{sort_field_name}> contain value <{self._data[sort_field_name]}>.'
                    f' But must contain value <{self.ASC_SORTING_VALUE}>'
                    f' or <{self.DESC_SORTING_VALUE}>.'
                )

    def make_statement(self) -> Select:
        self._add_filtration()
        self._add_interval_filtration()
        self._add_searching()
        self._add_sorting()
        return self.stmt
