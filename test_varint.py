import pytest

from app.varint import decode_varint


def huffman_decode(buffer, huffman_length=9):
    value, _ = decode_varint(buffer, huffman_length)
    return value


@pytest.mark.parametrize(
    "byte_tuple,expected",
    (
        ((0b0000_0000,), 0),
        ((0b0000_0001,), 1),
        ((0b1000_0000, 0b1000_0001), 129),
        ((0b1000_0001, 0b0000_0000), 256),
        ((0b1011_1111, 0b1111_1111), pow(2, 14) - 1),
        ((0b1111_1111, 0b1111_1111), -1),
        ((0b1100_0000, 0b0000_0000), -16384),
    ),
)
def test_15_bit_huffman(byte_tuple, expected):
    assert huffman_decode(bytearray(byte_tuple), 2) == expected


@pytest.mark.parametrize(
    "byte_tuple,expected",
    (
        ((0b0000_0000,), 0),
        ((0b0000_0001,), 1),
        ((0b1000_0001, 0b0000_0000), 128),
        ((0b1100_0000, 0b0000_0000), 8192),
        ((0b1000_0001, 0b1000_0000, 0b0000_0000), 32768),
        ((0b1000_0001, 0b1000_0000, 0b0000_0001), 32769),
        ((0b1010_0000, 0b1000_0000, 0b0000_0000), 1 << 20),
        ((0b1011_1111, 0b1111_1111, 0b1111_1111), (1 << 21) - 1),
        ((0b1111_1111, 0b1111_1111, 0b1111_1111), -1),
        ((0b1111_1111, 0b1100_0000, 0b0000_0000), -16384),
    ),
)
def test_23_bit_huffman(byte_tuple, expected):
    assert huffman_decode(bytearray(byte_tuple), 3) == expected


def test_64_bit_huffman():
    assert (
        huffman_decode(
            bytearray(
                (
                    0b1000_0001,
                    0b1000_0000,
                    0b1000_0000,
                    0b1000_0000,
                    0b1000_0000,
                    0b1000_0000,
                    0b1000_0000,
                    0b1000_0000,
                    0b0000_0000,
                )
            )
        )
        == 1 << 57
    )


@pytest.mark.parametrize("huffman_length", range(2, 10))
def test_max_huffman(huffman_length):
    assert (
        huffman_decode(
            bytearray((0b1011_1111,) + huffman_length * (0b1111_1111,)), huffman_length
        )
        == pow(2, 7 * huffman_length) - 1
    )


@pytest.mark.parametrize("huffman_length", range(2, 10))
def test_min_huffman(huffman_length):
    expected_value = -pow(2, 7 * huffman_length)
    assert huffman_decode(min_varint(huffman_length), huffman_length) == expected_value


@pytest.mark.parametrize("varint_length", range(2, 10))
def test_min_varint(varint_length):
    _, length = decode_varint(min_varint(varint_length), varint_length)
    assert length == varint_length


def min_varint(huffman_length):
    return bytearray(
        (0b1100_0000,) + (huffman_length - 2) * (0b1000_0000,) + (0b0000_0000,)
    )


@pytest.mark.parametrize("varint_length", range(2, 10))
def test_zero_varint(varint_length):
    _, length = decode_varint(bytearray((0b0000_0000,)), varint_length)
    assert length == 1


@pytest.mark.parametrize("low_byte", range(0, 127))
def test_problem_varint(low_byte):
    value, length = decode_varint(bytearray((0x81, low_byte, 0xB5, ord("n"), 0x0C)))
    assert length == 2
    assert value == 0x80 + low_byte


@pytest.mark.parametrize("low_byte", range(0, 127))
def test_ok_varint(low_byte):
    value, length = decode_varint(bytearray((0x80, low_byte, 0xB5, ord("n"), 0x0C)))
    assert length == 2
    assert value == low_byte
