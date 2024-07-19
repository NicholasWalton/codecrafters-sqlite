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