import pytest

from app.main import DbInfo, MIN_PAGE_SIZE

import sqlite3

from test_dbpage import build_test_database

DEFAULT_PAGE_SIZE = 4096


def test_page_size():
    assert DbInfo("sample.db").page_size == DEFAULT_PAGE_SIZE


def test_number_of_tables_in_sample():
    with sqlite3.connect("sample.db") as con:
        assert con.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(3,)]

    assert DbInfo("sample.db").number_of_tables == 3


@pytest.mark.parametrize("expected_tables", [
    1, 2, 5,  # Start at 1 because page_type is not in (5, 13) until we create a table!
    6,  # page 1 cell count still equal to table count
    7, 8,  # cell count changes to 0
    9,  # cell count changes to 1
    17,  # cell count changes to 2
    384,  # tree depth changes to 2
])
def test_number_of_tables(tmp_path, expected_tables):
    tmp_db_path = build_test_database(tmp_path, expected_tables)
    assert DbInfo(tmp_db_path).number_of_tables == expected_tables


def test_minimum_page_size(tmp_path):
    tmp_db_path = build_test_database(tmp_path, 1)
    assert DbInfo(tmp_db_path).page_size == MIN_PAGE_SIZE


def test_default_page_size(tmp_path):
    tmp_db_path = build_test_database(tmp_path, 1, page_size=DEFAULT_PAGE_SIZE)
    assert DbInfo(tmp_db_path).page_size == DEFAULT_PAGE_SIZE


