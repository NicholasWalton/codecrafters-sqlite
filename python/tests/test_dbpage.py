import sqlite3

import pytest

from codecrafters_sqlite.main import MIN_PAGE_SIZE, DbPage

TABLE_INTERIOR = 5
TABLE_LEAF = 13


def build_sqlite_schema_table(expected_tables):
    database_mmap = build_in_memory_test_database(
        expected_tables, page_size=MIN_PAGE_SIZE
    )
    page_one = DbPage(database_mmap, page_size=MIN_PAGE_SIZE)
    return page_one


def build_in_memory_test_database(expected_tables, **kwargs):
    with sqlite3.connect(":memory:") as db:
        create_tables(db, expected_tables, **kwargs)
        return db.serialize()


def build_test_database(tmp_path, expected_tables, **kwargs):
    tmp_db_path = tmp_path / "test.db"
    with sqlite3.connect(tmp_db_path) as db:
        create_tables(db, expected_tables, **kwargs)
    return tmp_db_path


def create_tables(db, count, page_size=MIN_PAGE_SIZE, row_count=0):
    db.execute("PRAGMA page_size = %d;" % page_size)
    for table in range(count):
        db.execute("CREATE TABLE dummy%d (value int);" % table)
        for row in range(row_count):
            db.execute(f"INSERT INTO dummy{table} VALUES(?)", (row,))
    db.commit()
    assert db.execute("SELECT count(*) FROM sqlite_schema").fetchall() == [(count,)]


def children_are_leaves(db_page: DbPage):
    return all(child.page_type == TABLE_LEAF for child in db_page.children)


@pytest.mark.parametrize("expected_tables", [1])
def test_table_names(expected_tables):
    page_one = build_sqlite_schema_table(expected_tables)
    assert page_one.child_rows == [
        ["table", "dummy0", "dummy0", 2, "CREATE TABLE dummy0 (value int)"]
    ]


@pytest.mark.parametrize("expected_tables", [6])
def test_sqlite_schema_table(expected_tables):
    page_one = build_sqlite_schema_table(expected_tables)
    assert len(page_one.children) == 0
    assert page_one.page_type == TABLE_LEAF
    assert page_one.number_of_cells == expected_tables


@pytest.mark.parametrize("expected_tables", [7, 8])
def test_sqlite_schema_table_spanning_two_pages(expected_tables):
    page_one = build_sqlite_schema_table(expected_tables)
    assert len(page_one.children) == 1
    assert all(child.page_type == TABLE_LEAF for child in page_one.children)
    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", range(9, 17))
def test_sqlite_schema_table_spanning_three_pages(expected_tables):
    page_one = build_sqlite_schema_table(expected_tables)
    assert len(page_one.children) == 2
    assert children_are_leaves(page_one)
    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", [17])
def test_sqlite_schema_table_spanning_four_pages(expected_tables):
    page_one = build_sqlite_schema_table(expected_tables)
    assert len(page_one.children) == 3
    assert children_are_leaves(page_one)
    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", [34, 68, 136, 272, 383])
def test_sqlite_schema_table_depth_one(expected_tables):
    page_one = build_sqlite_schema_table(expected_tables)
    assert len(page_one.children) > 0
    assert children_are_leaves(page_one)
    assert sum(child.number_of_cells for child in page_one.children) == expected_tables


@pytest.mark.parametrize("expected_tables", [384, 5003])
def test_sqlite_schema_table_spanning_more_depth(expected_tables):
    page_one = build_sqlite_schema_table(expected_tables)
    assert len(page_one.children) > 0
    assert any(child.page_type == TABLE_INTERIOR for child in page_one.children)


@pytest.mark.parametrize("expected_tables", [1, 5003])
def test_empty_last_table(expected_tables):
    sqlite_schema = build_sqlite_schema_table(expected_tables)
    assert len(sqlite_schema.child_rows) == expected_tables
    (type_, name, table_name, rootpage, sql) = sqlite_schema.child_rows[-1]
    assert type_ == "table"
    assert name == f"dummy{expected_tables - 1}"
    last_table = DbPage(sqlite_schema.database_file, rootpage, page_size=MIN_PAGE_SIZE)
    assert len(last_table.child_rows) == 0
