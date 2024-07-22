import sqlite3

import pytest

from app.main import MIN_PAGE_SIZE, DbInfo, extract_table_names
from test_dbpage import build_test_database

DEFAULT_PAGE_SIZE = 4096


def test_page_size():
    assert DbInfo("sample.db").page_size == DEFAULT_PAGE_SIZE


def test_tables_in_sample():
    with sqlite3.connect("sample.db") as con:
        assert con.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(3,)]

    db_info = DbInfo("sample.db")
    assert db_info.number_of_tables == 3
    assert db_info.table_names == ['apples', 'oranges']


@pytest.mark.parametrize(
    "expected_tables",
    [
        1,  # Start at 1 because page_type is not in (5, 13) until we create a table!
        2,
        5,
        6,  # page 1 cell count still equal to table count
        7,  # cell count changes to 0
        8,
        9,  # cell count changes to 1
        17,  # cell count changes to 2
        # 384,  # tree depth changes to 2
    ],
)
def test_number_of_tables(tmp_path, expected_tables):
    tmp_db_path = build_test_database(tmp_path, expected_tables)
    assert len(DbInfo(tmp_db_path).table_names) == expected_tables


def test_minimum_page_size(tmp_path):
    tmp_db_path = build_test_database(tmp_path, 1)
    assert DbInfo(tmp_db_path).page_size == MIN_PAGE_SIZE


def test_default_page_size(tmp_path):
    tmp_db_path = build_test_database(tmp_path, 1, page_size=DEFAULT_PAGE_SIZE)
    assert DbInfo(tmp_db_path).page_size == DEFAULT_PAGE_SIZE


def test_max_page_size(tmp_path):
    tmp_db_path = build_test_database(tmp_path, 1, page_size=65536)
    assert DbInfo(tmp_db_path).page_size == 65536


def test_extract_table_names():
    sqlite_schema = [['table', 'companies', 'companies', 2,
                      'CREATE TABLE companies\n(...)'],
                     ['table', 'sqlite_sequence', 'sqlite_sequence', 3, 'CREATE TABLE sqlite_sequence(name,seq)'],
                     ['index', 'idx_companies_country', 'companies', 4,
                      'CREATE INDEX idx_companies_country\n\ton companies (country)']]
    assert extract_table_names(sqlite_schema) == ['companies']


@pytest.mark.parametrize("size", [1, 384], )
def test_last_table(tmp_path, size):
    tmp_db_path = build_test_database(tmp_path, size, row_count=size)
    db_info = DbInfo(tmp_db_path)
    assert not db_info.find_table('no_such_table')
    last_table = db_info.find_table(f'dummy{size - 1}')
    assert len(last_table.child_rows) == size


@pytest.mark.parametrize("size", [1], )
def test_table_name_case_insensitive(tmp_path, size):
    tmp_db_path = build_test_database(tmp_path, size, row_count=size)
    db_info = DbInfo(tmp_db_path)
    table = db_info.find_table(f'dummy{size - 1}')
    assert db_info.find_table(f'DUMMY{size - 1}') == table
