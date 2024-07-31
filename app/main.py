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
        return list(self._generate_child_rows())

    @property
    def children(self):
        if self.page_type.is_interior():
            return list(self._generate_children())
        else:
            return []

    def _generate_child_rows(self):
        if self.page_type.is_leaf():
            for cell in range(self.number_of_cells):
                yield self._get_row(cell)
            if self._errors:
                self._log_leaf_page_errors(self.page_number)
        elif self.page_type.is_interior():
            for child_page in self._generate_children():
                yield from child_page._generate_child_rows()

    def _generate_children(self):
        if self.page_type.is_interior():
            for cell in range(self.number_of_cells):
                cell_content_pointer = self._cell_content_pointer(cell)
                yield self._child_at(cell_content_pointer)

            yield self._child_at(DbPage.RIGHT_MOST_POINTER_OFFSET)
        else:
            raise StopIteration

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

    def _get_row(self, cell_number):
        cell = TableLeafCell(
            self._page, self._cell_content_pointer(cell_number), self._usable_size
        )
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
    database_file_path = "../sample.db"
    if len(sys.argv) > 1:
        database_file_path = sys.argv[1]
    command = DotCommands.DBINFO
    if len(sys.argv) > 2:
        command = sys.argv[2]

    match command:
        case DotCommands.DBINFO:
            db_info = DbInfo(database_file_path)
            print(f"database page size: {db_info.page_size}")
            print(f"number of tables: {db_info.number_of_tables}")
        case DotCommands.TABLES:
            db_info = DbInfo(database_file_path)
            print(" ".join(db_info.table_names))
        case _:
            select_count = re.compile(r"SELECT COUNT\(\*\) FROM (\w+)", re.IGNORECASE)
            if (match := select_count.search(command)) is not None:
                (table_name,) = match.groups()
                print(len(DbInfo(database_file_path).find_table(table_name).child_rows))
            else:
                print(f"Invalid command: {command}")


if __name__ == "__main__":
    main()
