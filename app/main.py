import sys

from dataclasses import dataclass


# import sqlparse - available if you need it!

@dataclass
class DbInfo():
    page_size: int = 0
    number_of_tables: int = 0

    def __init__(self, database_file_path):
        with open(database_file_path, "rb") as database_file:
            database_file.seek(16)  # Skip the first 16 bytes of the header
            self.page_size = int.from_bytes(database_file.read(2), byteorder="big")
            database_file.seek(100)  # Skip database header
            page_type = int.from_bytes(database_file.read(1), byteorder="big")
            assert page_type == 13
            first_freeblock = int.from_bytes(database_file.read(2), byteorder="big")
            assert first_freeblock == 0
            number_of_cells = int.from_bytes(database_file.read(2), byteorder="big")
            self.number_of_tables = number_of_cells  # TODO: WRONG


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
