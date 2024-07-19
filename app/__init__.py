def _read_integer(database_file, offset, size):
    return int.from_bytes(database_file[offset: offset + size], byteorder="big")
