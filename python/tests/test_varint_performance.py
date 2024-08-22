import itertools
from mmap import mmap, ACCESS_READ

import codecrafters_sqlite._lowlevel
import pytest
from pathlib import Path
from timeit import timeit

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


# Theory: Rust is slower here because we pass in `bytes` instead of `bytearray`, leading to a copy
@pytest.mark.parametrize(*test_cases)
def test_read_bytes(varint_file: Path, decoder_to_test):
    timeit(lambda: assert_read_bytes(varint_file, decoder_to_test), number=1000)


def assert_read_bytes(varint_file, decoder_to_test):
    contents = varint_file.read_bytes()
    assert not (len(contents) % 9)
    assert len(contents) == 9 * 0xFF
    # Assert the 9th byte is 0 because the first time in our iterator it definitely
    # should be 0
    assert contents[8] == 0
    for expected, read_bytes in enumerate(itertools.batched(contents, 9)):
        value, length = decoder_to_test(read_bytes)
        assert value == expected
        assert length == 9


@pytest.mark.parametrize(*test_cases)
def test_mmap(varint_file, decoder_to_test):
    timeit(
        lambda: assert_mmap(varint_file=varint_file, decoder_to_test=decoder_to_test),
        number=100,
    )


@pytest.mark.parametrize(*test_cases)
def test_short_mmap(varint_file, decoder_to_test):
    timeit(
        lambda: assert_mmap(
            varint_file=varint_file,
            decoder_to_test=lambda varint_mmap: decoder_to_test(varint_mmap[:10]),
        ),
        number=100,
    )


def assert_mmap(varint_file, decoder_to_test):
    with open(varint_file, "rb") as varint_file:
        varint_mmap = mmap(varint_file.fileno(), 0, access=ACCESS_READ)
        varint_mmap = varint_mmap[:]  # Rust impl expects a slice every time
        for low_byte in range(0, 0xFF):  # 0 -> 255
            value, length = decoder_to_test(varint_mmap)
            assert value == low_byte
            assert length == 9
            varint_mmap = varint_mmap[length:]


@pytest.mark.parametrize(*test_cases)
def test_in_memory(decoder_to_test):
    timeit(
        lambda: assert_nine_byte_varints(decoder_to_test),
        number=1000,
    )


def assert_nine_byte_varints(decoder_to_test):
    for buffer in generate_varints():
        value, length = decoder_to_test(buffer)
        assert buffer[-1] == value
        assert length == 9


if __name__ == "__main__":
    pytest.main(args=[__file__, "--durations=0"])
