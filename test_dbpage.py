import os

import pytest

from app.main import DbPage, DbInfo

import sqlite3

def test_sqlite_schema_table_spanning_two_pages(tmp_path):
    tmp_db_path = tmp_path / "test.db"
    expected_tables = 65
    with sqlite3.connect(tmp_db_path) as db:
        for i in range(expected_tables):
            db.execute("CREATE TABLE dummy%d (value int);" % i)
        db.commit()
        assert db.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(expected_tables,)]

    with open(tmp_db_path, "rb") as database_file:
        assert DbInfo("sample.db").page_size == 4096
        page_one = DbPage(database_file)
        assert page_one.page_type == 5
        assert page_one.number_of_cells == 0
        assert page_one.child[0].page_type == 13
        assert page_one.child[0].number_of_cells == expected_tables
