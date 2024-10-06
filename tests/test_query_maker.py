from sqlalchemy import or_
from sqlalchemy import select

from src.db_first.query_maker import QueryMaker


def test_query_maker__init(fx_db):
    _, Parents, _, _ = fx_db

    qm = QueryMaker(Parents)
    assert qm.statement.compile().string == select(Parents).compile().string


def test_query_maker__filter(fx_db):
    _, Parents, _, _ = fx_db

    init_stmt = select(Parents)
    query_maker = QueryMaker(
        Parents, init_stmt, filter_by={'first': 'someone', 'second': ['someone']}
    )
    compiled_query_maker_stmt = query_maker.statement.compile().string

    compiled_control_stmt = (
        init_stmt.where(Parents.first == 'someone')
        .where(Parents.second.in_(['someone']))
        .compile()
        .string
    )

    assert compiled_query_maker_stmt in compiled_control_stmt


def test_query_maker__interval_filter(fx_db):
    _, Parents, _, _ = fx_db

    query_maker = QueryMaker(
        Parents, interval_filter_by={'start_first': 'start_someone', 'end_first': 'end_someone'}
    )
    compiled_query_maker_stmt = query_maker.statement.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.first >= 'end_someone')
        .where(Parents.first < 'start_someone')
        .compile()
        .string
    )

    assert compiled_query_maker_stmt == compiled_control_stmt


def test_query_maker__search_filter(fx_db):
    _, Parents, _, _ = fx_db

    query_maker = QueryMaker(Parents, search_by={'first': 'someone', 'second': 'someone'})
    compiled_query_maker_stmt = query_maker.statement.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(or_(Parents.first.ilike('%someone%'), Parents.second.ilike('%someone%')))
        .compile()
        .string
    )

    assert compiled_query_maker_stmt == compiled_control_stmt


def test_query_maker__sort(fx_db):
    _, Parents, _, _ = fx_db

    query_maker = QueryMaker(Parents, sort_by={'first': 'asc', 'second': 'desc'})
    compiled_query_maker_stmt = query_maker.statement.compile().string

    compiled_control_stmt = (
        select(Parents).order_by(Parents.first).order_by(Parents.second.desc()).compile().string
    )

    assert compiled_query_maker_stmt == compiled_control_stmt


def test_query_maker__limit(fx_db):
    _, Parents, _, _ = fx_db

    query_maker = QueryMaker(Parents, limit=1)
    compiled_query_maker_stmt = query_maker.statement.compile().string

    compiled_control_stmt = select(Parents).limit(1).compile().string

    assert compiled_query_maker_stmt == compiled_control_stmt


def test_query_maker__offset(fx_db):
    _, Parents, _, _ = fx_db

    query_maker = QueryMaker(Parents, offset=1)
    compiled_query_maker_stmt = query_maker.statement.compile().string

    compiled_control_stmt = select(Parents).offset(1).compile().string

    assert compiled_query_maker_stmt == compiled_control_stmt
