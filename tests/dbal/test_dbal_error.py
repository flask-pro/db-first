from uuid import uuid4

import pytest

from src.db_first.dbal.exceptions import DBALCreateException
from src.db_first.dbal.exceptions import DBALObjectNotFoundException
from src.db_first.dbal.exceptions import DBALUpdateException
from tests.conftest import UNIQUE_STRING

wrong_data = [
    {'unknown': 'unknown', 'first': next(UNIQUE_STRING)},
    {'': 'unknown', 'first': next(UNIQUE_STRING)},
    {'first': [1, 2, 3]},
    {'first': {'key': 'value'}},
]


@pytest.mark.parametrize('data', wrong_data)
def test_dbal__create_error(fx_db, fx_parent_dbal, data):
    session_db, parents_model, _, _ = fx_db

    with pytest.raises(DBALCreateException):
        fx_parent_dbal(session_db).create(**data)


@pytest.mark.parametrize('data', [{'first': [1, 2, 3]}])
def test_dbal__bulk_create_error(fx_db, fx_parent_dbal, data):
    session_db, parents_model, _, _ = fx_db

    with pytest.raises(DBALCreateException):
        fx_parent_dbal(session_db).bulk_create([data])


def test_dbal__read_error(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    with pytest.raises(DBALObjectNotFoundException):
        fx_parent_dbal(session_db).read(uuid4())


@pytest.mark.parametrize('data', wrong_data)
def test_dbal__update_error(fx_db, fx_parent_dbal, data):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(session_db).create(**params)

    updated_params = data

    with pytest.raises(DBALUpdateException):
        fx_parent_dbal(session_db).update(new.id, **updated_params)


@pytest.mark.parametrize('data', [{'first': [1, 2, 3]}])
def test_dbal__bulk_update_error(fx_db, fx_parent_dbal, data):
    session_db, parents_model, _, _ = fx_db

    params = {'first': next(UNIQUE_STRING)}
    new = fx_parent_dbal(session_db).create(**params)

    updated_params = [{'id': new.id, **data}]
    with pytest.raises(DBALUpdateException):
        fx_parent_dbal(session_db).bulk_update(updated_params)


def test_dbal__bulk_update_non_exist_id_error(fx_db, fx_parent_dbal):
    session_db, parents_model, _, _ = fx_db

    data = {'first': next(UNIQUE_STRING)}
    updated_params = [{'id': uuid4(), **data}]
    with pytest.raises(DBALObjectNotFoundException):
        fx_parent_dbal(session_db).bulk_update(updated_params)
