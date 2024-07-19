import pytest

def huffman_decode(varint, huffman_length = 2):
    unsigned = 0

    byte_index = 0
    while byte_index < huffman_length - 1 and _high_bit(varint[byte_index]):
        unsigned = (unsigned << 7) + (_lower7(varint[byte_index]))
        byte_index += 1

    unsigned = (unsigned << 8) + varint[byte_index]

    huffman_bits = 7 * huffman_length + 1
    sign_bit = 1 << (huffman_bits - 1)
    if unsigned & sign_bit:
        return unsigned - (sign_bit << 1)
    return unsigned


def _high_bit(byte):
    return byte & 0b1000_0000


def _lower7(byte):
    return byte & 0b0111_1111


@pytest.mark.parametrize("byte_tuple,expected", (
        ((0b0000_0000,), 0),
        ((0b0000_0001,), 1),
        ((0b1000_0000, 0b1000_0001), 129),
        ((0b1000_0001, 0b0000_0000), 256),
        ((0b1011_1111, 0b1111_1111), pow(2, 14) - 1),
        ((0b1111_1111, 0b1111_1111), -1),
        ((0b1100_0000, 0b0000_0000), -16384),
))
def test_15_bit_huffman(byte_tuple, expected):
    assert huffman_decode(bytearray(byte_tuple)) == expected


@pytest.mark.parametrize("byte_tuple,expected", (
        ((0b0000_0000,), 0),
        ((0b0000_0001,), 1),
        ((0b1000_0001, 0b0000_0000), 256),
        ((0b1100_0000, 0b0000_0000), 16384),
        ((0b1000_0001, 0b1000_0000, 0b0000_0000), 32768),
))
def test_23_bit_huffman(byte_tuple, expected):
    assert huffman_decode(bytearray(byte_tuple), 3) == expected


def test_max_23_bit_huffman():
    assert huffman_decode(bytearray((0b1011_1111, 0b1111_1111, 0b1111_1111)), 3) == (pow(2, 22)) - 1


def test_64_bit_huffman():
    assert huffman_decode(bytearray((0b1000_0001, 0b1000_0000, 0b1000_0000,
                                     0b1000_0000, 0b1000_0000, 0b1000_0000,
                                     0b1000_0000, 0b1000_0000, 0b0000_0000)), 9) == 1 << 57


def test_max_64_bit_huffman():
    assert huffman_decode(bytearray((0b1011_1111, 0b1111_1111, 0b1111_1111,
                                     0b1111_1111, 0b1111_1111, 0b1111_1111,
                                     0b1111_1111, 0b1111_1111, 0b1111_1111)), 9) == (pow(2, 63)) - 1
