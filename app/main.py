import sys

from dataclasses import dataclass

# import sqlparse - available if you need it!


def main():
    database_file_path = sys.argv[1]
    command = sys.argv[2]

    if command == ".dbinfo":
        page_size = db_info(database_file_path)
        print(f"database page size: {page_size}")
    else:
        print(f"Invalid command: {command}")


def db_info(database_file_path):
    with open(database_file_path, "rb") as database_file:
        database_file.seek(16)  # Skip the first 16 bytes of the header
        page_size = int.from_bytes(database_file.read(2), byteorder="big")
        return page_size


if __name__ == '__main__':
    main()