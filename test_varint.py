
def huffman_decode(varint):
    if _high_bit(varint[0]):
        return (_lower7(varint[0]) << 8) + varint[1]
    return varint[0]

def _high_bit(byte):
    return byte & 0b1000_0000

def _lower7(byte):
    return (byte & 0b0111_1111)

def test_zero_value_15_bit_huffman():
    assert huffman_decode(bytearray((0b0000_0000,))) == 0

def test_one_value_15_bit_huffman():
    assert huffman_decode(bytearray((0b0000_0001,))) == 1

def test_two_byte_15_bit_huffman():
    assert huffman_decode(bytearray((0b1000_0000, 0b1000_0001))) == 129

def test_256_value_15_bit_huffman():
    assert huffman_decode(bytearray((0b1000_0001, 0b0000_0000))) == 256
