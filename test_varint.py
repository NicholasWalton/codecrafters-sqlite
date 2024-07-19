import pytest

def huffman_decode(varint):
    if _high_bit(varint[0]):
        unsigned = (_lower7(varint[0]) << 8) + varint[1]
        if unsigned & (1 << 14):
            return unsigned - (1 << 15)
            # raise Exception("Negative!")
        return unsigned
    return varint[0]

def _high_bit(byte):
    return byte & 0b1000_0000

def _lower7(byte):
    return (byte & 0b0111_1111)

@pytest.mark.parametrize("byte_tuple,expected", (
        ((0b0000_0000,), 0),
        ((0b0000_0001,), 1),
        ((0b1000_0000, 0b1000_0001), 129),
        ((0b1000_0001, 0b0000_0000), 256),
        ((0b1011_1111, 0b1111_1111), 16383),
        ((0b1111_1111, 0b1111_1111), -1),
        ((0b1100_0000, 0b0000_0000), -16384),
))
def test_15_bit_huffman(byte_tuple, expected):
    assert huffman_decode(bytearray(byte_tuple)) == expected
