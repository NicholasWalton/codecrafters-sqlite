import pytest

from app.main import DbInfo

import sqlite3


def test_page_size():
    assert DbInfo("sample.db").page_size == 4096


def test_number_of_tables_in_sample():
    with sqlite3.connect("sample.db") as con:
        assert con.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(3,)]

    assert DbInfo("sample.db").number_of_tables == 3


@pytest.mark.parametrize("expected_tables", [
    1, 2, 5, # Start at 1 because page_type is not in (5, 13) until we create a table!
    6,  # page 1 cell count still equal to table count
    7, 8,  # cell count changes to 0
    9,  # cell count changes to 1
    # 131,  # TODO: find where cell count changes from 1 to 2
])
def test_number_of_tables(tmp_path, expected_tables):
    tmp_db_path = build_test_database(tmp_path, expected_tables, page_size=512)
    assert DbInfo(tmp_db_path).number_of_tables == expected_tables


def test_minimum_page_size(tmp_path):
    tmp_db_path = build_test_database(tmp_path, 1, 512)
    assert DbInfo(tmp_db_path).page_size == 512


def build_test_database(tmp_path, expected_tables, page_size=4096):
    tmp_db_path = tmp_path / "test.db"
    with sqlite3.connect(tmp_db_path) as db:
        db.execute("PRAGMA page_size = %d;" % page_size)
        for i in range(expected_tables):
            db.execute("CREATE TABLE dummy%d (value int);" % i)
        db.commit()
        assert db.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(expected_tables,)]
    return tmp_db_path
