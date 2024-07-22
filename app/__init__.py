def _read_integer(database_file, offset, size, **kwargs):
    return int.from_bytes(database_file[offset: offset + size], byteorder="big", **kwargs)
