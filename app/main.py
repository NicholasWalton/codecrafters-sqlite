import re
import sys
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from mmap import ACCESS_READ, mmap

from app import _read_integer
from app.cells import TableLeafCell


class DotCommands(StrEnum):
    DBINFO = ".dbinfo"
    TABLES = ".tables"


PAGE_SIZE_OFFSET = 16

# import sqlparse - available if you need it!

CELL_POINTER_SIZE = 2
MIN_PAGE_SIZE = 512


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
            self.sqlite_schema = sqlite_schema_tree_root.child_rows
            self.table_names = extract_table_names(self.sqlite_schema)
            self.number_of_tables = len(self.sqlite_schema)

    def find_table(self, requested_name):
        for (type_, name, table_name, rootpage, sql) in self.sqlite_schema:
            if type_ == 'table' and name.casefold() == requested_name.casefold():
                return self._table(rootpage)

    def _table(self, rootpage):
        return DbPage(self.database_mmap, page_number=rootpage, page_size=self.page_size)


def extract_table_names(sqlite_schema):
    return [name for type_, name, *_
            in sqlite_schema
            if type_ == 'table' and not name.startswith('sqlite_')
            ]


@dataclass
class DbPage:
    number_of_cells: int = 0
    page_size: int = -1

    RIGHT_MOST_POINTER_OFFSET = 8

    def __init__(self, database_file, page_number=1, page_size=4096, usable_size=4096):
        self.child_rows = []
        self.page_size = page_size
        self.usable_size = usable_size
        self.database_file = database_file
        self.page_content_cells_offset = self.page_size * (page_number - 1)
        self.page_offset = 100 if page_number == 1 else self.page_content_cells_offset
        self.page = database_file[self.page_offset: self.page_content_cells_offset + self.page_size]

        self.page_type = PageType(self._read_integer(0, 1))
        assert self.page_type.is_table()
        first_freeblock = self._read_integer(1, 2)
        # assert first_freeblock == 0
        self.number_of_cells = self._read_integer(3, 2)
        cell_content_area_start = self._read_integer(5, 2)
        self.cell_content_area_start = (
            65536 if cell_content_area_start == 0 else cell_content_area_start
        )
        cell_pointer_array = self.page[self.page_type.cell_pointer_array_offset():self.page_type.cell_pointer_array_offset()+2*self.number_of_cells]
        unallocated = self.page[self.page_type.cell_pointer_array_offset()+2*self.number_of_cells:self.cell_content_area_start]
        cell_content_area = self.page[self.cell_content_area_start:]

        self.children = []
        if self.page_type.is_leaf():
            for cell in range(self.number_of_cells):
                self.child_rows.append(self._get_row(cell))
        elif self.page_type.is_interior():
            for cell in range(self.number_of_cells):
                cell_content_pointer = self.get_cell_content_pointer(cell)
                self._add_child_at(cell_content_pointer)

            self._add_child_at(DbPage.RIGHT_MOST_POINTER_OFFSET)

    def _get_row(self, cell_number):
        # if self.page_offset == 20480 and cell_number >= 10:
        #     pass
        cell_pointer_location = (
                cell_number * CELL_POINTER_SIZE
                + self.page_type.cell_pointer_array_offset()
        )

        cell_offset = self._read_integer(cell_pointer_location, CELL_POINTER_SIZE)
        cell_location = cell_offset + self.page_content_cells_offset - self.page_offset
        cell = TableLeafCell(self.page, cell_location, self.usable_size)
        return cell.columns

    def get_cell_content_pointer(self, cell):
        cell_pointer_location = (
                cell * CELL_POINTER_SIZE
                + self.page_type.cell_pointer_array_offset()
        )
        cell_offset = self._read_integer(cell_pointer_location, CELL_POINTER_SIZE)
        return cell_offset + self.page_content_cells_offset - self.page_offset

    def _read_integer(self, location_in_page, size):
        return _read_integer(self.page, location_in_page, size)

    def _add_child_at(self, child_page_number_location):
        child_page_number = self._read_integer(child_page_number_location, 4)
        child_page = DbPage(self.database_file, child_page_number, self.page_size)
        self.children.append(child_page)
        self.child_rows += child_page.child_rows


def main():
    database_file_path = "../companies.db"
    if len(sys.argv) > 1:
        database_file_path = sys.argv[1]
    command = "SELECT COUNT(*) FROM companies"
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
                table_name, = match.groups()
                print(len(DbInfo(database_file_path).find_table(table_name).child_rows))
            else:
                print(f"Invalid command: {command}")


if __name__ == "__main__":
    main()
