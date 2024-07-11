from app.main import DbPage, DbInfo

from test_dbinfo import build_test_database


def test_sqlite_schema_table_spanning_two_pages(tmp_path):
    tmp_db_path = tmp_path / "test.db"
    expected_tables = 65
    tmp_db_path = build_test_database(tmp_path, expected_tables)

    with open(tmp_db_path, "rb") as database_file:
        page_one = DbPage(database_file)
        assert page_one.page_type == 5
        assert page_one.number_of_cells == 0
        assert page_one.child[0].page_type == 13
        assert page_one.child[0].number_of_cells == expected_tables
