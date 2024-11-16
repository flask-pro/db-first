from datetime import datetime
from datetime import timedelta
from math import ceil

import pytest
import sqlalchemy
from db_first import BaseCRUD
from db_first.mixins import CreateMixin
from db_first.mixins import PaginationMixin
from sqlalchemy import select

from .conftest import UNIQUE_STRING


def test_controller__pagination_without_metadata(fx_parent_controller):
    fx_parent_controller.create(data={'first': next(UNIQUE_STRING)})
    fx_parent_controller.create(data={'first': next(UNIQUE_STRING)})

    items = fx_parent_controller.paginate()
    assert not items.get('_metadata')

    for item in items['items']:
        assert item.id


def test_controller__pagination(fx_parents__non_deletion, fx_parent_controller):
    total_items_number = 10
    ids = [fx_parents__non_deletion().id for _ in range(total_items_number)]

    items = fx_parent_controller.paginate(
        page=1, per_page=2, max_per_page=20, include_metadata=True, id=ids
    )
    assert items['items']
    assert len(items['items']) == 2
    assert items['_metadata']['pagination']['page'] == 1
    assert items['_metadata']['pagination']['per_page'] == 2
    assert items['_metadata']['pagination']['pages'] == total_items_number / 2
    assert items['_metadata']['pagination']['total'] == total_items_number


def test_controller__sorting(fx_parents__non_deletion, fx_parent_controller):
    _ = [fx_parents__non_deletion() for _ in range(10)]

    items = fx_parent_controller.paginate(sort_created_at='asc')
    asc_first_item = items['items'][0].id
    items = fx_parent_controller.paginate(sort_created_at='desc')
    desc_first_item = items['items'][0].id
    assert asc_first_item != desc_first_item


def test_controller__searching(fx_parents__non_deletion, fx_parent_controller):
    new_item = fx_parents__non_deletion()
    fx_parents__non_deletion()

    items = fx_parent_controller.paginate(search=new_item.first)
    for item in items['items']:
        assert item.first == new_item.first


def test_controller__get_fields_of_list(fx_db, fx_parent_controller):
    _, _, _, Fathers = fx_db

    fx_parent_controller.create(data={'first': next(UNIQUE_STRING)})

    fields = ['id']
    items = fx_parent_controller.paginate(fields=fields, serialize=True)
    assert items['items']

    for item in items['items']:
        assert list(item) == fields


def test_controller__filtrating(fx_parents__non_deletion, fx_parent_controller):
    first_item = fx_parents__non_deletion()
    _ = [fx_parents__non_deletion() for _ in range(10)]

    patched_item_payload = {'id': first_item.id, 'first': 'first for test filtrating'}
    patched_first_item = fx_parent_controller.update(data=patched_item_payload)

    items = fx_parent_controller.paginate(first=patched_first_item.first)
    assert len(items['items']) == 1
    assert items['items'][0].id == first_item.id

    items = fx_parent_controller.paginate(page=1, per_page=1, first=patched_first_item.first)
    assert items['items']
    assert items['items'][0].id == first_item.id


def test_controller__interval_filtration(fx_parent_controller):
    item_first = fx_parent_controller.create(data={'first': next(UNIQUE_STRING)})
    item_second = fx_parent_controller.create(data={'first': next(UNIQUE_STRING)})
    item_third = fx_parent_controller.create(data={'first': next(UNIQUE_STRING)})

    items_asc = fx_parent_controller.paginate(
        include_metadata=True,
        id=[item_first.id, item_second.id, item_third.id],
        sort_created_at='asc',
        start_created_at=item_first.created_at,
        end_created_at=item_third.created_at,
    )
    assert items_asc['_metadata']['pagination']['page'] == 1
    assert items_asc['_metadata']['pagination']['pages'] == 1
    assert items_asc['items']
    assert len(items_asc['items']) == 2
    assert items_asc['items'][0].id == item_first.id
    assert items_asc['items'][1].id == item_second.id

    items_desc = fx_parent_controller.paginate(
        include_metadata=True,
        id=[item_first.id, item_second.id, item_third.id],
        sort_created_at='desc',
        start_created_at=item_first.created_at,
        end_created_at=item_third.created_at,
    )
    assert items_desc['_metadata']['pagination']['page'] == 1
    assert items_desc['_metadata']['pagination']['pages'] == 1
    assert items_desc['items']
    assert len(items_desc['items']) == 2
    assert items_desc['items'][0].id == item_second.id
    assert items_desc['items'][1].id == item_first.id


@pytest.mark.parametrize('page', [-1, 0, 1_000_000])
@pytest.mark.parametrize('per_page', [-1, 0, 1_000_000])
def test_controller__get_over_page(fx_parent_controller, page, per_page):
    fx_parent_controller.create(data={'first': next(UNIQUE_STRING)})

    items = fx_parent_controller.paginate(page=page, per_page=per_page, include_metadata=True)
    assert items['_metadata']['pagination']['page'] == page

    if per_page <= 0:
        assert items['_metadata']['pagination']['per_page'] == per_page
        assert items['_metadata']['pagination']['pages'] == 0
        assert items['_metadata']['pagination']['total'] == 0
    if per_page > 100:
        assert items['_metadata']['pagination']['per_page'] == 100

        total = items['_metadata']['pagination']['total']
        assert items['_metadata']['pagination']['pages'] == ceil(total / 100)

    assert not items['items']


def test_controller__without_meta_pagination(fx_db, fx_parent_schema_of_create):
    db_session, Parents, _, _ = fx_db

    class CustomController(CreateMixin, PaginationMixin, BaseCRUD):
        class Meta:
            model = Parents
            statement = select(model)
            session = db_session
            input_schema_of_create = fx_parent_schema_of_create

    custom_controller = CustomController()
    custom_controller.create(data={'first': next(UNIQUE_STRING)})

    items = custom_controller.paginate(fields=['id'])
    assert '_metadata' not in items
    assert items['items']


def test_controller__statement(
    fx_db, fx_parent_schema_of_create, fx_parents__non_deletion, fx_parent_controller
):
    session, Parents, Children, _ = fx_db

    total_items_number = 10
    ids = [fx_parents__non_deletion().id for _ in range(total_items_number)]

    statement = sqlalchemy.select(Parents).join(Children)

    items = fx_parent_controller.paginate(
        statement=statement,
        page=1,
        per_page=2,
        max_per_page=20,
        include_metadata=True,
        id=ids,
        sort_created_at='desc',
        search='name',
        start__created_at=datetime.utcnow() - timedelta(minutes=1),
        end__created_at=datetime.utcnow(),
    )
    assert items['items']
    assert len(items['items']) == 2
    assert items['_metadata']['pagination']['page'] == 1
    assert items['_metadata']['pagination']['per_page'] == 2
    assert items['_metadata']['pagination']['pages'] == total_items_number / 2
    assert items['_metadata']['pagination']['total'] == total_items_number


def test_controller__fields_for_relations(
    fx_parent_controller, fx_child_controller, fx_father_controller
):
    new_father = fx_father_controller.create(data={'first': next(UNIQUE_STRING)})
    new_parent = fx_parent_controller.create(
        data={'first': next(UNIQUE_STRING), 'father_id': new_father.id}
    )
    new_child = fx_child_controller.create(
        data={'first': next(UNIQUE_STRING), 'parent_id': new_parent.id}
    )

    items = fx_parent_controller.paginate(id=new_parent.id, serialize=True)
    assert len(items['items']) == 1
    assert items['items'][0]['id'] == str(new_parent.id)
    assert items['items'][0]['created_at'] == new_parent.created_at.isoformat()
    assert items['items'][0]['father'] == {
        'id': str(new_father.id),
        'first': new_father.first,
        'created_at': new_father.created_at.isoformat(),
    }
    assert items['items'][0]['children'] == [
        {'id': str(new_child.id), 'first': new_child.first, 'parent_id': str(new_parent.id)}
    ]
