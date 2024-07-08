import pytest

import app.main

import sqlite3


def test_page_size():
    assert app.main.DbInfo("sample.db").page_size == 4096


def test_number_of_tables():
    with sqlite3.connect("sample.db") as con:
        assert con.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(3,)]

    assert app.main.DbInfo("sample.db").number_of_tables == 3


# Start at 1 because page_type is not 13 until we create a table!
@pytest.mark.parametrize("expected_tables", range(1, 4))
def test_far_too_many_tables(tmp_path, expected_tables):
    # expected_tables = 3
    tmp_db_path = tmp_path / "test.db"
    with sqlite3.connect(tmp_db_path) as db:
        for i in range(expected_tables):
            db.execute("CREATE TABLE dummy%d (value int);" % i)
        db.commit()
        assert db.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(expected_tables,)]
    assert app.main.DbInfo(tmp_db_path).number_of_tables == expected_tables
