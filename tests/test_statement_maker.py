from sqlalchemy import or_
from sqlalchemy import select

from src.db_first.statement_maker import StatementMaker


def test_statement_maker__init(fx_db):
    _, Parents, _, _ = fx_db

    stmt = StatementMaker(Parents, data={})
    assert stmt.stmt.compile().string == select(Parents).compile().string


def test_statement_maker__filter(fx_db):
    _, Parents, _, _ = fx_db

    init_stmt = select(Parents)
    statement_maker = StatementMaker(
        Parents,
        data={'first': 'someone', 'second': ['someone']},
        statement=init_stmt,
        filterable_fields=['first', 'second'],
    )
    compiled_stmt = statement_maker.stmt.compile().string

    compiled_control_stmt = (
        init_stmt.where(Parents.first == 'someone')
        .where(Parents.second.in_(['someone']))
        .compile()
        .string
    )

    assert compiled_stmt in compiled_control_stmt


def test_statement_maker__interval_filter(fx_db):
    _, Parents, _, _ = fx_db

    stmt = StatementMaker(
        Parents,
        data={'start_first': 'start_someone', 'end_first': 'end_someone'},
        interval_filterable_fields=['first'],
    ).make_statement()
    compiled_stmt = stmt.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(Parents.first >= 'end_someone')
        .where(Parents.first < 'start_someone')
        .compile()
        .string
    )

    assert compiled_stmt == compiled_control_stmt


def test_statement_maker__search_filter(fx_db):
    _, Parents, _, _ = fx_db

    stmt = StatementMaker(
        Parents,
        data={'search_first': 'someone', 'search_second': 'someone'},
        searchable_fields=['first', 'second'],
    ).make_statement()
    compiled_stmt = stmt.compile().string

    compiled_control_stmt = (
        select(Parents)
        .where(or_(Parents.first.ilike('%someone%'), Parents.second.ilike('%someone%')))
        .compile()
        .string
    )

    assert compiled_stmt == compiled_control_stmt


def test_statement_maker__sort(fx_db):
    _, Parents, _, _ = fx_db

    stmt = StatementMaker(
        Parents,
        data={'sort_first': 'asc', 'sort_second': 'desc'},
        sortable_fields=['first', 'second'],
    ).make_statement()
    compiled_stmt = stmt.compile().string

    compiled_control_stmt = (
        select(Parents).order_by(Parents.first).order_by(Parents.second.desc()).compile().string
    )

    assert compiled_stmt == compiled_control_stmt
