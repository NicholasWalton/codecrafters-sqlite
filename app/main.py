import itertools
import logging
import re
import struct
import sys
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from mmap import ACCESS_READ, mmap
from pprint import pformat

from app import _buffer, _read_integer
from app.cells import TableLeafCell

SAMPLE_DB = "sample.db"


class DotCommands(StrEnum):
    DBINFO = ".dbinfo"
    TABLES = ".tables"


PAGE_SIZE_OFFSET = 16

# import sqlparse - available if you need it!

CELL_POINTER_SIZE = 2
MIN_PAGE_SIZE = 512

logger = logging.getLogger(__name__)


class PageType(IntEnum):
    INDEX_INTERIOR = 2
    TABLE_INTERIOR = 5
    INDEX_LEAF = 10
    TABLE_LEAF = 13

    def is_interior(self):
        return self in (PageType.TABLE_INTERIOR, PageType.INDEX_INTERIOR)

    def is_table(self):
        return self in (PageType.TABLE_LEAF, PageType.TABLE_INTERIOR)

    def is_leaf(self):
        return not self.is_interior()

    def is_index(self):
        return not self.is_table()

    def cell_pointer_array_offset(self):
        return 12 if self.is_interior() else 8


@dataclass
class DbInfo:
    page_size: int = 0

    def __init__(self, database_file_path):
        with open(database_file_path, "rb") as database_file:
            self.database_mmap = mmap(database_file.fileno(), 0, access=ACCESS_READ)
            self.page_size = _read_integer(self.database_mmap, PAGE_SIZE_OFFSET, 2)
            self.page_size = 65536 if self.page_size == 1 else self.page_size
            sqlite_schema_tree_root = self._table(1)
            self._sqlite_schema = sqlite_schema_tree_root.child_rows
            self.table_names = extract_table_names(self._sqlite_schema)
            self.number_of_tables = len(self._sqlite_schema)

    def find_table(self, requested_name):
        if requested_name == "sqlite_schema":
            return self._table(1)
        for type_, name, table_name, rootpage, sql in self._sqlite_schema:
            if type_ == "table" and name.casefold() == requested_name.casefold():
                return self._table(rootpage)

    def _table(self, rootpage):
        return DbPage(
            self.database_mmap, page_number=rootpage, page_size=self.page_size
        )


def extract_table_names(sqlite_schema):
    return [
        name
        for type_, name, *_ in sqlite_schema
        if type_ == "table" and not name.startswith("sqlite_")
    ]


@dataclass
class DbPage:
    number_of_cells: int = 0
    _page_size: int = -1

    RIGHT_MOST_POINTER_OFFSET = 8

    def __init__(self, database_file, page_number=1, page_size=4096, usable_size=4096):
        self._errors = 0
        self._page_size = page_size
        self._usable_size = usable_size
        self.database_file = database_file
        self._page_number = page_number

        self._page = database_file[
            self._page_offset : self._page_content_cells_offset + self._page_size
        ]

        page_type, first_freeblock, self.number_of_cells, cell_content_area_start = (
            struct.unpack_from(">BHHH", self._page)
        )
        self.page_type = PageType(page_type)
        assert self.page_type.is_table()
        # assert first_freeblock == 0
        self.cell_content_area_start = (
            65536 if cell_content_area_start == 0 else cell_content_area_start
        )

        self._cell_pointer_array = _buffer(
            self._page,
            self.page_type.cell_pointer_array_offset(),
            CELL_POINTER_SIZE * self.number_of_cells,
        )

        logging.debug(f"Reading page {self._page_number}")

    @property
    def child_rows(self):
        return list(cell.columns for cell in self._generate_child_rows())

    @property
    def children(self):
        return list(self._generate_children())

    def _generate_child_rows(self):
        for child_page in self._generate_children():
            yield from child_page._generate_child_rows()
        if self.page_type.is_leaf():
            for cell in range(self.number_of_cells):
                yield self._cell(cell)
            if self._errors:
                self._log_leaf_page_errors(self.page_number)

    def _generate_children(self):
        if self.page_type.is_interior():
            for cell in range(self.number_of_cells):
                cell_content_pointer = self._cell_content_pointer(cell)
                yield self._child_at(cell_content_pointer)

            yield self._child_at(DbPage.RIGHT_MOST_POINTER_OFFSET)

    def _log_leaf_page_error(self, page_number):
        logger.error(f"{self._errors} errors in page {page_number}")
        cell_pointer_array = _buffer(
            self._page,
            self.page_type.cell_pointer_array_offset(),
            CELL_POINTER_SIZE * self.number_of_cells,
        )
        pairs = zip(*([iter(cell_pointer_array)] * 2))
        cell_pointers = list(
            int.from_bytes(pointer, byteorder="big") for pointer in pairs
        )
        logger.error(f"Page {page_number} cell pointer array:{pformat(cell_pointers)}")
        logger.debug(f"Page {page_number} rows:\n{pformat(self.child_rows, indent=4)}")

    @property
    def _page_content_cells_offset(self):
        return self._page_size * (self._page_number - 1)

    @property
    def _page_offset(self):
        return 100 if self._page_number == 1 else self._page_content_cells_offset

    @property
    def _cell_content_offset(self):
        return self._page_offset - self._page_content_cells_offset

    def _cell(self, cell_number):
        return TableLeafCell(
            self._page, self._cell_content_pointer(cell_number), self._usable_size
        )

    def _get_row(self, cell_number):
        cell = self._cell(cell_number)
        logging.debug(f"Cell {cell_number}: {cell.columns[:2]}")
        self._errors += cell.errors
        if cell.errors:
            self._log_cell_errors(cell_number, cell)
        return cell.columns

    def _log_cell_errors(self, cell_number, cell):
        logger.error(
            f"{cell.errors} errors in cell {cell_number} at +{self._cell_content_pointer(cell_number)} on page {self._page_number}"
        )
        logger.debug(f"Cell {cell_number} columns:\n{pformat(cell.columns, indent=4)}")

    def _cell_content_pointer(self, cell):
        cell_offset = _read_integer(
            self._cell_pointer_array, cell * CELL_POINTER_SIZE, CELL_POINTER_SIZE
        )
        return cell_offset - self._cell_content_offset

    def _read_integer(self, location_in_page, size):
        return _read_integer(self._page, location_in_page, size)

    def _child_at(self, child_page_number_location):
        child_page_number = self._read_integer(child_page_number_location, 4)
        child_page = DbPage(self.database_file, child_page_number, self._page_size)
        return child_page


def main():
    logging.basicConfig(level=logging.INFO)
    database_file_path = SAMPLE_DB
    if len(sys.argv) > 1:
        database_file_path = sys.argv[1]
    command = DotCommands.DBINFO
    if len(sys.argv) > 2:
        command = sys.argv[2]

    db_info = DbInfo(database_file_path)
    match command:
        case DotCommands.DBINFO:
            print(f"database page size: {db_info.page_size}")
            print(f"number of tables: {db_info.number_of_tables}")
        case DotCommands.TABLES:
            print(" ".join(db_info.table_names))
        case _:
            for line in handle(command, database_file_path):
                print(line)


def handle(sql, database_file_path):
    """Handle a SQL query

    >>> list(handle("select count(*) from apples", SAMPLE_DB))
    [4]
    >>> list(handle("select * from apples", SAMPLE_DB))
    [[1, 'Granny Smith', 'Light Green'], [2, 'Fuji', 'Red'], [3, 'Honeycrisp', 'Blush Red'], [4, 'Golden Delicious', 'Yellow']]
    >>> list(handle("select name from apples", SAMPLE_DB))
    ['Granny Smith', 'Fuji', 'Honeycrisp', 'Golden Delicious']
    """
    db_info = DbInfo(database_file_path)
    select_count = re.compile(
        r"SELECT COUNT\(\*\) FROM (?P<table_name>\w+)", re.IGNORECASE
    )
    select_star = re.compile(r"SELECT \* FROM (?P<table_name>\w+)", re.IGNORECASE)
    select_column = re.compile(
        r"SELECT (?P<column>\w+) FROM (?P<table_name>\w+)", re.IGNORECASE
    )
    if (match := select_count.search(sql)) is not None:
        table_name = match.group("table_name")
        child_rows = db_info.find_table(table_name)._generate_child_rows()
        batched = itertools.batched(child_rows, 1000)
        yield sum(map(len, batched))
    elif (match := select_star.search(sql)) is not None:
        table_name = match.group("table_name")
        yield from db_info.find_table(table_name).child_rows
    elif (match := select_column.search(sql)) is not None:
        table_name = match.group("table_name")
        column_name = match.group("column")
        yield from (row[1] for row in db_info.find_table(table_name).child_rows)
    else:
        yield f"Invalid command: {sql}"


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    main()

"""
[
    'table',
    'companies',
    'companies',
    2,
    'CREATE TABLE companies\n(\n\tid integer primary key autoincrement\n, name text, domain text, year_founded text, industry text, "size range" text, locality text, country text, current_employees text, total_employees text)'
]
"""
