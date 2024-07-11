
import pytest

from app.main import DbPage

from test_dbinfo import build_test_database

TABLE_INTERIOR = 5
TABLE_LEAF = 13

MIN_PAGE_SIZE = 512


def test_sqlite_schema_table(tmp_path):
    expected_tables = 6
    tmp_db_path = build_test_database(tmp_path, expected_tables, page_size=512)

    with open(tmp_db_path, "rb") as database_file:
        page_one = DbPage(database_file, page_size=MIN_PAGE_SIZE)
    assert page_one.page_type == TABLE_LEAF
    assert page_one.number_of_cells == expected_tables
    assert len(page_one.children) == 0


@pytest.mark.parametrize("expected_tables", [7, 8])
def test_sqlite_schema_table_spanning_two_pages(tmp_path, expected_tables):
    tmp_db_path = build_test_database(tmp_path, expected_tables, page_size=MIN_PAGE_SIZE)

    with open(tmp_db_path, "rb") as database_file:
        page_one = DbPage(database_file, page_size=MIN_PAGE_SIZE)
    assert len(page_one.children) == 1
    assert all(child.page_type == TABLE_LEAF for child in page_one.children)
    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", range(9, 17))
def test_sqlite_schema_table_spanning_three_pages(tmp_path, expected_tables):
    tmp_db_path = build_test_database(tmp_path, expected_tables, page_size=MIN_PAGE_SIZE)

    with open(tmp_db_path, "rb") as database_file:
        page_one = DbPage(database_file, page_size=MIN_PAGE_SIZE)
    assert len(page_one.children) == 2
    assert all(child.page_type == TABLE_LEAF for child in page_one.children)
    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", [17])
def test_sqlite_schema_table_spanning_four_pages(tmp_path, expected_tables):
    tmp_db_path = build_test_database(tmp_path, expected_tables, page_size=MIN_PAGE_SIZE)
    with open(tmp_db_path, "rb") as database_file:
        page_one = DbPage(database_file, page_size=MIN_PAGE_SIZE)
    assert all(child.page_type == TABLE_LEAF for child in page_one.children)
    assert page_one.number_of_cells == 2
    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", [34, 68, 136, 272, 383])
def test_sqlite_schema_table_depth_one(tmp_path, expected_tables):
    tmp_db_path = build_test_database(tmp_path, expected_tables, page_size=MIN_PAGE_SIZE)

    with open(tmp_db_path, "rb") as database_file:
        page_one = DbPage(database_file, page_size=MIN_PAGE_SIZE)
    assert len(page_one.children) > 0
    assert all(child.page_type == TABLE_LEAF for child in page_one.children)

    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", [384])
def test_sqlite_schema_table_spanning_more_depth(tmp_path, expected_tables):
    # try:
    #     os.remove('./test.db')
    # except FileNotFoundError:
    #     pass
    # tmp_db_path = build_test_database(Path('.'), expected_tables, page_size=512)

    tmp_db_path = build_test_database(tmp_path, expected_tables, page_size=MIN_PAGE_SIZE)
    with open(tmp_db_path, "rb") as database_file:
        page_one = DbPage(database_file, page_size=MIN_PAGE_SIZE)
    assert len(page_one.children) > 0
    assert any(child.page_type == TABLE_INTERIOR for child in page_one.children)
