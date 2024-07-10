import sys

from dataclasses import dataclass


# import sqlparse - available if you need it!

@dataclass
class DbInfo:
    page_size: int = 0
    number_of_tables: int = 0

    def __init__(self, database_file_path):
        with open(database_file_path, "rb") as database_file:
            database_file.seek(16)  # Skip the first 16 bytes of the header
            self.page_size = int.from_bytes(database_file.read(2), byteorder="big")
            self.number_of_tables = DbPage(database_file).number_of_cells # TODO: Wrong


@dataclass
class DbPage:
    number_of_cells: int = 0

    def __init__(self, database_file, offset = 100, page_size = 4096):
        database_file.seek(offset)  # Skip database header
        self.page_type = int.from_bytes(database_file.read(1), byteorder="big")
        assert self.page_type in (5, 13)
        first_freeblock = int.from_bytes(database_file.read(2), byteorder="big")
        assert first_freeblock == 0
        self.number_of_cells = int.from_bytes(database_file.read(2), byteorder="big")
        cell_content_area_start = int.from_bytes(database_file.read(2), byteorder="big") # TODO: special case
        offset_of_cell_pointer_array = 12 if self.page_type in (2, 5) else 8
        if self.page_type in (2, 5):
            self.child = []
            database_file.seek(offset + 8)
            right_most_child_page = int.from_bytes(database_file.read(4), byteorder="big") - 1
            database_file.seek(offset + offset_of_cell_pointer_array)
            cell_offset = int.from_bytes(database_file.read(2), byteorder="big")
            database_file.seek(cell_content_area_start + cell_offset)
            child_count = 0
            for i in range(self.number_of_cells):
                page_of_child = int.from_bytes(database_file.read(-1), byteorder="big")
                child_count += 1
                offset_of_child = page_of_child * page_size
                self.child.append(DbPage(database_file, offset_of_child))
                database_file.seek(offset + offset_of_cell_pointer_array + 4 * child_count)
            self.child.append(DbPage(database_file, right_most_child_page * page_size))

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
