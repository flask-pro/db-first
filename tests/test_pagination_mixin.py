from datetime import timezone
from math import ceil
from uuid import UUID

import marshmallow
import pytest

from tests.conftest import UNIQUE_STRING


def test_controller__pagination(fx_parent_action__create, fx_parent_action__paginate):
    ids = [fx_parent_action__create({'first': next(UNIQUE_STRING)}).run().id for _ in range(3)]

    data = {'page': 0, 'per_page': 2, 'ids': ids, 'fields': ['items.id', 'items.first']}
    items = fx_parent_action__paginate(data).run()

    assert items['items']
    assert len(items['items']) == 2
    for item in items['items']:
        assert UUID(item['id'])
        assert isinstance(item['first'], str)

    data = {'page': 1, 'per_page': 2, 'ids': ids, 'fields': ['items.id', 'items.first']}
    items = fx_parent_action__paginate(data).run()

    assert items['items']
    assert len(items['items']) == 1
    for item in items['items']:
        assert UUID(item['id'])
        assert isinstance(item['first'], str)


def test_controller__sorting(fx_parent_action__create, fx_parent_action__paginate):
    ids = [fx_parent_action__create({'first': next(UNIQUE_STRING)}).run().id for _ in range(3)]

    data = {'ids': ids, 'sort__created_at': 'asc'}
    items_asc = fx_parent_action__paginate(data).run()
    asc_ids = [item['id'] for item in items_asc['items']]

    data = {'ids': ids, 'sort__created_at': 'desc'}
    items_desc = fx_parent_action__paginate(data).run()
    desc_ids = [item['id'] for item in items_desc['items']]

    assert asc_ids[0] == desc_ids[-1]


def test_controller__searching(fx_parent_action__create, fx_parent_action__paginate):
    new_item = fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()
    fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()
    search_substring = new_item.first[3:]

    data = {'fields': ['items.id', 'items.first'], 'contain__first': search_substring}
    items = fx_parent_action__paginate(data).run()
    for item in items['items']:
        assert search_substring in item['first']


def test_controller__get_fields_of_list(
    fx_db, fx_parent_action__create, fx_parent_action__paginate
):
    _, _, _, Fathers = fx_db
    fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()

    data = {'fields': ['items.id', 'items.first']}
    items = fx_parent_action__paginate(data).run()

    assert list(items['items'][0]) == ['id', 'first']


def test_controller__filtrating(
    fx_parent_action__create, fx_parent_action__update, fx_parent_action__paginate
):
    first_item = fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()
    _ = [fx_parent_action__create({'first': next(UNIQUE_STRING)}).run() for _ in range(10)]

    patched_item_payload = {'id': first_item.id, 'first': 'first for test filtrating'}
    patched_first_item = fx_parent_action__update(patched_item_payload).run()

    data = {'eq__first': patched_first_item.first}
    items = fx_parent_action__paginate(data).run()

    assert len(items['items']) == 1
    assert items['items'][0]['id'] == str(first_item.id)


def test_controller__interval_filtration(fx_parent_action__create, fx_parent_action__paginate):
    item_1 = fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()
    item_2 = fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()
    item_3 = fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()

    data = {
        'ids': [item_1.id, item_2.id, item_3.id],
        'sort__created_at': 'asc',
        'ge__created_at': item_1.created_at.replace(tzinfo=timezone.utc),
        'le__created_at': item_2.created_at.replace(tzinfo=timezone.utc),
    }
    items_asc = fx_parent_action__paginate(data).run()

    assert items_asc['items']
    assert len(items_asc['items']) == 2
    assert items_asc['items'][0]['id'] == str(item_1.id)
    assert items_asc['items'][1]['id'] == str(item_2.id)

    data = {
        'ids': [item_1.id, item_2.id, item_3.id],
        'sort__created_at': 'desc',
        'ge__created_at': item_1.created_at.replace(tzinfo=timezone.utc),
        'le__created_at': item_2.created_at.replace(tzinfo=timezone.utc),
    }
    items_desc = fx_parent_action__paginate(data).run()

    assert items_desc['items']
    assert len(items_desc['items']) == 2
    assert items_desc['items'][0]['id'] == str(item_2.id)
    assert items_desc['items'][1]['id'] == str(item_1.id)


@pytest.mark.parametrize('page', [-1])
@pytest.mark.parametrize('per_page', [-1, 0])
def test_controller__get_non_exist_page(
    fx_parent_action__create, fx_parent_action__paginate, page, per_page
):
    fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()

    data = {'page': page, 'per_page': per_page, 'include_metadata': 'enable'}
    with pytest.raises(marshmallow.exceptions.ValidationError):
        fx_parent_action__paginate(data).run()


@pytest.mark.parametrize('page', [0, 1])
@pytest.mark.parametrize('per_page', [1, 2])
def test_controller__get_pages(
    fx_parent_action__create, fx_parent_action__paginate, page, per_page
):
    fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()
    fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()

    data = {'page': page, 'per_page': per_page, 'include_metadata': 'enable'}
    items = fx_parent_action__paginate(data).run()

    assert items['_metadata']['pagination']['page'] == page
    assert items['_metadata']['pagination']['per_page'] == per_page
    assert items['_metadata']['pagination']['pages'] == ceil(
        items['_metadata']['pagination']['total'] / per_page
    )
    assert items['_metadata']['pagination']['total'] > 1
    assert items['items']


def test_controller__without_meta_pagination(
    fx_db, fx_parent_action__create, fx_parent_action__paginate
):
    fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()
    fx_parent_action__create({'first': next(UNIQUE_STRING)}).run()

    data = {'page': 0, 'per_page': 2}
    items = fx_parent_action__paginate(data).run()

    assert '_metadata' not in items
    assert items['items']


def test_controller__fields_for_relations(
    fx_parent_action__create,
    fx_child_action__create,
    fx_father_action__create,
    fx_parent_action__paginate,
):
    new_father_1 = fx_father_action__create({'first': next(UNIQUE_STRING)}).run()
    new_parent_1 = fx_parent_action__create(
        {'first': next(UNIQUE_STRING), 'father_id': new_father_1.id}
    ).run()
    fx_child_action__create({'first': next(UNIQUE_STRING), 'parent_id': new_parent_1.id}).run()

    new_father = fx_father_action__create({'first': next(UNIQUE_STRING)}).run()
    new_parent = fx_parent_action__create(
        {'first': next(UNIQUE_STRING), 'father_id': new_father.id}
    ).run()
    new_child = fx_child_action__create(
        {'first': next(UNIQUE_STRING), 'parent_id': new_parent.id}
    ).run()

    data = {
        'fields': [
            'items.id',
            'items.second',
            'items.created_at',
            'items.father.id',
            'items.father.created_at',
            'items.children.id',
            'items.children.parent_id',
        ],
        'eq__id': new_parent.id,
    }
    items = fx_parent_action__paginate(data).run()

    assert len(items['items']) == 1
    assert items['items'][0]['id'] == str(new_parent.id)
    assert items['items'][0].get('second') is None
    assert items['items'][0]['created_at'] == new_parent.created_at.isoformat()
    assert items['items'][0]['father'] == {
        'id': str(new_father.id),
        'created_at': new_father.created_at.isoformat(),
    }
    assert items['items'][0]['children'] == [
        {'id': str(new_child.id), 'parent_id': str(new_parent.id)}
    ]
