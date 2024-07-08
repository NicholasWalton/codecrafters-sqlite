import app.main

import sqlite3

def test_page_size():
    assert app.main.DbInfo("sample.db").page_size == 4096


def test_number_of_tables():
    with sqlite3.connect("sample.db") as con:
        assert con.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(3,)]

    # assert app.main.DbInfo("sample.db").number_of_tables == 3
