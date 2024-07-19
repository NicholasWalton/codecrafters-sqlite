
def huffman_decode(varint):
    if varint[0] & 0b1000_0000:
        return ((varint[0] & 0b0111_1111) << 8) + varint[1]
    return varint[0]

def test_zero_value_15_bit_huffman():
    assert huffman_decode(bytearray((0b0000_0000,))) == 0

def test_one_value_15_bit_huffman():
    assert huffman_decode(bytearray((0b0000_0001,))) == 1

def test_two_byte_15_bit_huffman():
    assert huffman_decode(bytearray((0b1000_0000, 0b1000_0001))) == 129

def test_256_value_15_bit_huffman():
    assert huffman_decode(bytearray((0b1000_0001, 0b0000_0000))) == 256
