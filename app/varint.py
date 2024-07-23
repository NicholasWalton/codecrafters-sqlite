def varint_at(bytearray_slice, offset):
    return varint_decode(bytearray_slice[offset: offset + 9])


def varint_decode(varint, huffman_length=9):
    unsigned = 0

    for byte_index in range(huffman_length - 1):  # zero or more bytes which have the high-order bit set
        unsigned = (unsigned << 7) + _lower7(varint[byte_index])  # The lower seven bits of each of the first n-1 bytes
        if not _high_bit(varint[byte_index]):  # including a single end byte with the high-order bit clear
            break
    else:
        byte_index += 1
        unsigned = (unsigned << 8) + varint[byte_index]  # or all 8 bits of the nth byte

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
