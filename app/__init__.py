def _read_integer(bytes_, offset, size, **kwargs):
    return int.from_bytes(bytes_[offset: offset + size], byteorder="big", **kwargs)
