def varint_at(bytearray_slice, offset):
    return varint_decode(bytearray_slice[offset: offset + 9])


def varint_decode(varint, huffman_length=9):
    unsigned = 0

    byte_index = 0
    while byte_index < huffman_length - 1 and _high_bit(varint[byte_index]):
        unsigned = (unsigned << 7) + (_lower7(varint[byte_index]))
        byte_index += 1

    if byte_index == huffman_length - 1:
        unsigned = (unsigned << 8) + varint[byte_index]
    else:
        unsigned = (unsigned << 7) + varint[byte_index]

    huffman_bits = 7 * huffman_length + 1
    sign_bit = 1 << (huffman_bits - 1)
    if unsigned & sign_bit:
        value = unsigned - (sign_bit << 1)
    else:
        value = unsigned

    return value, byte_index + 1


def _high_bit(byte):
    return byte & 0b1000_0000


def _lower7(byte):
    return byte & 0b0111_1111
