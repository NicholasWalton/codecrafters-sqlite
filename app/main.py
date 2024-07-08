import sys

from dataclasses import dataclass


# import sqlparse - available if you need it!

@dataclass
class DbInfo():
    page_size: int = 0

def main():
    database_file_path = sys.argv[1]
    command = sys.argv[2]

    if command == ".dbinfo":
        page_size = db_info(database_file_path)
        print(f"database page size: {page_size}")
    else:
        print(f"Invalid command: {command}")


def db_info(database_file_path):
    db_info = DbInfo()
    with open(database_file_path, "rb") as database_file:
        database_file.seek(16)  # Skip the first 16 bytes of the header
        db_info.page_size = int.from_bytes(database_file.read(2), byteorder="big")
    return db_info


if __name__ == '__main__':
    main()
