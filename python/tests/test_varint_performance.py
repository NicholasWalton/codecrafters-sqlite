import itertools
from pathlib import Path
from timeit import timeit

import pytest

from codecrafters_sqlite._lowlevel import decode_varint as rust_decode_varint


def main():
    print(f"Python: {test_python()} sec")
    print(f"Rust:   {test_rust()} sec")


def test_python():
    setup = "from codecrafters_sqlite.varint import decode_varint"
    nine_byte_varints(setup)


def test_rust():
    setup = "from codecrafters_sqlite._lowlevel import decode_varint"
    nine_byte_varints(setup)


@pytest.fixture()
def varint_file(tmp_path):
    bytes_to_write = b"".join(buffer for buffer in generate_bytes())
    (tmp_path / "varints.bin").write_bytes(bytes_to_write)
    return tmp_path / "varints.bin"


def test_read_file(varint_file: Path):
    contents = varint_file.read_bytes()
    assert not (len(contents) % 9)
    assert len(contents) == 9 * 0xFF

    # Assert the 9th byte is 0 because the first time in our iterator it definitely
    # should be 0
    assert contents[8] == 0

    for expected, read_bytes in enumerate(itertools.batched(contents, 9)):
        value, length = rust_decode_varint(read_bytes)
        assert value == expected
        assert length == 9


def generate_bytes():
    for low_byte in range(0, 0xFF):  # 0 -> 255
        yield bytearray((0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, low_byte))


def nine_byte_varints(setup):
    stmt = """
for low_byte in range(0, 0xFF):
    buffer = bytearray((0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, low_byte))
    value, length = decode_varint(buffer)
    assert low_byte == value
    assert length == 9
"""
    return timeit(
        stmt,
        setup,
        number=1000,
    )


if __name__ == "__main__":
    pytest.pytest()
