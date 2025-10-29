from datetime import datetime

import pytest


def test_model_mixin__to_dict(fx_parents__non_deletion):
    new_parent = fx_parents__non_deletion()

    assert new_parent.to_dict(
        {
            'id': ...,
            'first': ...,
            'father': {'id': ..., 'first': ...},
            'children': [{'id': ..., 'first': ...}],
        }
    ) == {
        'id': new_parent.id,
        'first': new_parent.first,
        'father': {'first': new_parent.father.first, 'id': new_parent.father.id},
        'children': [{'first': new_parent.children[0].first, 'id': new_parent.children[0].id}],
    }


@pytest.mark.parametrize('date_time', ['', None, 'not_date_time', datetime.now()])
def test_model_mixin__validate_timezone(fx_db, date_time):
    session, _, _, Fathers = fx_db

    with pytest.raises(ValueError) as e:
        Fathers(first='first', created_at=date_time)

    assert e.value.args[0] == (
        'Field <created_at> must be datetime with UTC timezone, but received timezone: <None>'
    )
