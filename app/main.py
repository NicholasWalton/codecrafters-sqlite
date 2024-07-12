import sys

from dataclasses import dataclass
from enum import IntEnum

CELL_POINTER_SIZE = 2

RIGHT_MOST_POINTER_OFFSET = 8


# import sqlparse - available if you need it!

def _read_next_integer(database_file, size):
    return int.from_bytes(database_file.read(size), byteorder="big")


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
    number_of_tables: int = 0

    def __init__(self, database_file_path):
        with open(database_file_path, "rb") as database_file:
            database_file.seek(16)  # Skip the first 16 bytes of the header
            self.page_size = _read_next_integer(database_file, 2)
            self.number_of_tables = DbPage(database_file, page_size=self.page_size).number_of_cells  # TODO: Wrong


@dataclass
class DbPage:
    number_of_cells: int = 0
    page_size: int = -1

    def __init__(self, database_file, page_number=1, page_size=4096):
        self.page_size = page_size
        page_content_cells_offset = self.page_size * (page_number - 1)
        page_offset = 100 if page_number == 1 else page_content_cells_offset

        database_file.seek(page_offset)  # Skip database header
        self.page_type = PageType(_read_next_integer(database_file, 1))
        assert self.page_type.is_table()
        first_freeblock = _read_next_integer(database_file, 2)
        # assert first_freeblock == 0
        self.number_of_cells = _read_next_integer(database_file, 2)
        cell_content_area_start = _read_next_integer(database_file, 2)  # TODO: special case

        self.children = []
        if self.page_type.is_interior():
            for cell in range(self.number_of_cells):
                cell_pointer_location = cell * CELL_POINTER_SIZE + self.page_type.cell_pointer_array_offset() + page_offset
                database_file.seek(cell_pointer_location)
                cell_offset = _read_next_integer(database_file, CELL_POINTER_SIZE)
                self._add_child_at(cell_offset + page_content_cells_offset, database_file)

            self._add_child_at(page_offset + RIGHT_MOST_POINTER_OFFSET, database_file)

    def _add_child_at(self, child_page_number_location, database_file):
        database_file.seek(child_page_number_location)
        child_page_number = _read_next_integer(database_file, 4)
        child_page = DbPage(database_file, child_page_number, page_size=self.page_size)
        self.children.append(child_page)


def main():
    database_file_path = sys.argv[1]
    command = sys.argv[2]

    if command == ".dbinfo":
        page_size = DbInfo(database_file_path).page_size
        print(f"database page size: {page_size}")
    else:
        print(f"Invalid command: {command}")


if __name__ == '__main__':
    main()
