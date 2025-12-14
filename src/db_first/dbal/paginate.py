from math import ceil
from typing import Any

import sqlalchemy as sa
from sqlalchemy import func

from ..statement_maker import StatementMaker


class PageMixin:
    """Read objects from database as page."""

    _filter_prefixes = ['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in']

    _search_prefixes = ['contain']

    _sort_prefixes = ['sort']
    _asc_value = 'asc'
    _desc_value = 'desc'

    def _extract_expressions(self, params: dict[str, Any]):
        order_by = []
        filters = []
        for name, value in params.items():
            prefix, param = name.split('__')
            if prefix in self._filter_prefixes:
                filters.append({'col': param, 'opr': prefix, 'value': value})
            elif prefix in self._sort_prefixes:
                order_by.append({'col': param, 'opr': value})
            elif prefix in self._search_prefixes:
                filters.append({'col': param, 'opr': 'ilike', 'value': value})
            else:
                raise NotImplementedError(f'Expression for parameter <{name}> not implemented.')

        return order_by, filters

    def query_string_to_sql_json(
        self,
        page: int,
        per_page: int,
        ids: list[str] | None = None,
        **params: dict[str, Any],
    ) -> dict[str, Any]:
        sql_as_json = {'limit': per_page, 'offset': per_page * page}

        order_by, filters = self._extract_expressions(params)

        if ids:
            filters.append({'col': 'id', 'opr': 'in', 'value': ids})

        if filters:
            sql_as_json['where'] = {'and': filters}

        if order_by:
            sql_as_json['order_by'] = order_by

        return sql_as_json

    def run_query(self, **data: dict[str, Any]):
        stmt = StatementMaker(self._model, **data).make_stmt()
        return self._session.scalars(stmt).all()

    def paginate(
        self,
        ids: list[str] | None = None,
        page: int = 0,
        per_page: int = 1000,
        include_metadata: bool = False,
        **data: dict[str, Any],
    ) -> dict[str, Any]:
        sql_as_json = self.query_string_to_sql_json(ids=ids, page=page, per_page=per_page, **data)

        items = self.run_query(**sql_as_json)

        result = {'items': items}

        if include_metadata:
            total = self._session.scalar(
                sa.select(func.count()).select_from(self._model).order_by(None)
            )

            pages = ceil(total / per_page)

            result['_metadata'] = {
                'pagination': {'page': page, 'per_page': per_page, 'pages': pages, 'total': total}
            }

        return result
