import itertools
from mmap import mmap, ACCESS_READ

import codecrafters_sqlite._lowlevel
import pytest
from pathlib import Path
from timeit import timeit

SQLITE_I64_VARINT_LENGTH = 9

NUMBER = 1000

test_cases = (
    "decoder_to_test",
    (
        pytest.param(codecrafters_sqlite.varint.decode_varint, id="python"),
        pytest.param(codecrafters_sqlite._lowlevel.decode_varint, id="rust"),
    ),
)


@pytest.fixture()
def varint_file(tmp_path):
    tmp_file = tmp_path / "varints.bin"
    bytes_to_write = b"".join(buffer for buffer in generate_varints())
    tmp_file.write_bytes(bytes_to_write)
    return tmp_file


def generate_varints():
    for low_byte in range(0, 0xFF):  # 0 -> 255
        yield bytearray((0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, low_byte))


@pytest.mark.parametrize(*test_cases)
def test_read_bytes(varint_file: Path, decoder_to_test):
    timeit(lambda: assert_read_bytes(varint_file, decoder_to_test), number=NUMBER)


def assert_read_bytes(varint_file, decoder_to_test):
    contents = varint_file.read_bytes()
    assert not (len(contents) % SQLITE_I64_VARINT_LENGTH)
    assert len(contents) == SQLITE_I64_VARINT_LENGTH * 0xFF
    # Assert the 9th byte is 0 because the first time in our iterator it definitely
    # should be 0
    assert contents[SQLITE_I64_VARINT_LENGTH - 1] == 0
    for expected, read_bytes in enumerate(
            itertools.batched(contents, SQLITE_I64_VARINT_LENGTH)
    ):
        assert_decode(bytearray(read_bytes), decoder_to_test, expected)


@pytest.mark.parametrize(*test_cases)
def test_mmap(varint_file, decoder_to_test):
    timeit(lambda: assert_mmap(varint_file, decoder_to_test), number=NUMBER)


@pytest.mark.parametrize(*test_cases)
def test_short_mmap(varint_file, decoder_to_test):
    def slice_and_decode(varint_mmap):
        return decoder_to_test(varint_mmap[: SQLITE_I64_VARINT_LENGTH + 1])

    timeit(lambda: assert_mmap(varint_file, slice_and_decode), number=NUMBER)


def assert_mmap(varint_file, decoder_to_test):
    with open(varint_file, "rb") as varint_file:
        varint_mmap = mmap(varint_file.fileno(), 0, access=ACCESS_READ)
        varint_mmap = varint_mmap[:]  # Rust impl expects a slice every time
        for low_byte in range(0, 0xFF):  # 0 -> 255
            length = assert_decode(varint_mmap, decoder_to_test, low_byte)
            varint_mmap = varint_mmap[length:]


@pytest.mark.parametrize(*test_cases)
def test_in_memory(decoder_to_test):
    timeit(lambda: assert_nine_byte_varints(decoder_to_test), number=NUMBER)


def assert_nine_byte_varints(decoder_to_test):
    for buffer in generate_varints():
        assert_decode(buffer, decoder_to_test, buffer[-1])


def assert_decode(buffer, decoder_to_test, expected):
    value, length = decoder_to_test(buffer)
    assert expected == value
    assert length == SQLITE_I64_VARINT_LENGTH
    return length


if __name__ == "__main__":
    pytest.main(args=[__file__, "--durations=0"])
