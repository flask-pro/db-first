from math import ceil
from typing import Optional

from sqlalchemy import func
from sqlalchemy import Select
from sqlalchemy import select

from ..exc import OptionNotFound
from ..query_maker import QueryMaker


class PaginationMixin:
    """Mixin added method `paginate` for get paginated result.

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

    `filterable` - list of fields allowed for filtration.
    `interval_filterable` - list of fields allowed for filtration interval.
    `sortable` - list of fields allowed for sorting.
    `searchable` - a list of fields allowed for search for by substring.
    `schema_of_paginate` - marshmallow schema for serialize.
    """

    SORT_PREFIX = 'sort_'

    def _extract_filterable_params(self, **kwargs) -> dict:
        filterable_params = {}

        try:
            fields = self._get_option_from_meta('filterable')
        except OptionNotFound:
            return filterable_params

        for field in fields:
            if field in kwargs:
                filterable_params[field] = kwargs[field]

        return filterable_params

    def _extract_interval_filterable_params(self, **kwargs) -> Optional[dict]:
        interval_filterable_params = {}

        try:
            fields = self._get_option_from_meta('interval_filterable')
        except OptionNotFound:
            return interval_filterable_params

        for field in fields:
            start_field_name = f'start_{field}'
            if start_field_name in kwargs:
                interval_filterable_params[start_field_name] = kwargs[start_field_name]

            end_field_name = f'end_{field}'
            if end_field_name in kwargs:
                interval_filterable_params[end_field_name] = kwargs[end_field_name]

        return interval_filterable_params

    def _extract_sortable_params(self, **kwargs) -> Optional[dict]:
        sortable_params = {}

        try:
            fields = self._get_option_from_meta('sortable')
        except OptionNotFound:
            return sortable_params

        for field in fields:
            field_name_of_sorting = f'{self.SORT_PREFIX}{field}'
            if field_name_of_sorting in kwargs:
                sortable_params[field] = kwargs[field_name_of_sorting]

        return sortable_params

    def _extract_searchable_params(self, search: str) -> Optional[dict]:
        fields = self._get_option_from_meta('searchable')
        searchable_params = {field: search for field in fields}
        return searchable_params

    def _calculate_items_per_page(self, statement: Select, per_page: int) -> tuple[int, int]:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        total = session.execute(
            statement.with_only_columns(func.count()).order_by(None).select_from(model)
        ).scalar_one()

        pages = ceil(total / per_page)

        return pages, total

    def _make_metadata(self, page, per_page, statement):
        pages, total = self._calculate_items_per_page(statement, per_page)

        return {'pagination': {'page': page, 'per_page': per_page, 'pages': pages, 'total': total}}

    def paginate(
        self,
        statement: Optional[Select] = None,
        page: int = 1,
        per_page: Optional[int] = 20,
        max_per_page: Optional[int] = 100,
        serialize: bool = False,
        search: Optional[str] = ...,
        include_metadata: bool = False,
        fields: Optional[list] = None,
        **kwargs,
    ) -> dict:
        session = self._get_option_from_meta('session')
        model = self._get_option_from_meta('model')

        if per_page > max_per_page:
            per_page = max_per_page

        items = {'items': []}
        if page <= 0 or per_page <= 0:
            if include_metadata:
                items['_metadata'] = {
                    'pagination': {'page': page, 'per_page': per_page, 'pages': 0, 'total': 0}
                }
            return items

        filter_by = self._extract_filterable_params(**kwargs)
        interval_filter_by = self._extract_interval_filterable_params(**kwargs)
        sort_by = self._extract_sortable_params(**kwargs)

        if search is not Ellipsis:
            search_by = self._extract_searchable_params(search)
        else:
            search_by = None

        if statement is None:
            statement = select(model)

        stmt = QueryMaker(
            model,
            statement=statement,
            filter_by=filter_by,
            interval_filter_by=interval_filter_by,
            sort_by=sort_by,
            search_by=search_by,
        ).statement

        if include_metadata:
            items['_metadata'] = self._make_metadata(page, per_page, stmt)

        stmt = stmt.limit(per_page).offset((page - 1) * per_page)
        paginated_rows = session.scalars(stmt).all()

        if serialize:
            items['items'] = self.serialize_data('schema_of_paginate', paginated_rows, fields)
        else:
            items['items'] = paginated_rows

        return items
