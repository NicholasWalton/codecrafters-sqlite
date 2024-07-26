def _read_integer(bytes_, offset, size, **kwargs):
    return int.from_bytes(bytes_[offset: offset + size], byteorder="big", **kwargs)

def _buffer(sequence, start, size):
    return sequence[start : start + size]