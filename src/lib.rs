use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

const HUFFMAN_LENGTH: usize = 9;

#[pyfunction]
fn varint(buffer: Vec<u8>) -> PyResult<(i64, usize)> {
    let mut acc = 0i64;

    let mut byte_index = decode_leading_bytes(&buffer, &mut acc);
    if byte_index == HUFFMAN_LENGTH - 1 {
        // or all 8 bits of the nth byte
        acc = (acc << 8) + buffer[byte_index] as i64;
    }
    let huffman_bits = 7 * HUFFMAN_LENGTH + 1;
    let sign_bit = 1 << (huffman_bits - 1);
    if (acc & sign_bit) != 0 {
        Ok((acc - (sign_bit << 1), byte_index + 1))
    } else {
        Ok((acc, byte_index + 1))
    }
}

fn decode_leading_bytes(buffer: &Vec<u8>, acc: &mut i64) -> usize {
    // zero or more bytes which have the high-order bit set
    for byte_index in 0..HUFFMAN_LENGTH - 1 {
        // The lower seven bits of each of the first n-1 byte
        *acc = (*acc << 7) + _lower7(buffer.get(byte_index).unwrap()) as i64;
        // including a single end byte with the high-order bit clear
        if 0 == _high_bit(buffer.get(byte_index).unwrap()) {
            return byte_index;
        }
    }
    HUFFMAN_LENGTH - 1
}

fn _high_bit(byte: &u8) -> u8 {
    byte & 0b1000_0000
}

fn _lower7(byte: &u8) -> u8 {
    byte & 0b0111_1111
}

/// A Python module implemented in Rust.
#[pymodule]
fn codecrafters_sqlite(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    m.add_function(wrap_pyfunction!(varint, m)?)?;
    Ok(())
}

#[cfg(test)]
mod test {
    use crate::varint;

    #[test]
    fn zero() {
        assert_eq!(varint(vec![0]).unwrap().0, 0i64);
    }

    #[test]
    fn one() {
        assert_eq!(varint(vec![1]).unwrap().0, 1i64);
    }

    #[test]
    fn eight_bits() {
        assert_eq!(varint(vec![0b1000_0001, 0b0000_0000]).unwrap().0, 128i64);
    }

    #[test]
    fn nine_bytes() {
        assert_eq!(
            varint(vec![
                0b1000_0001,
                0b1000_0000,
                0b1000_0000,
                0b1000_0000,
                0b1000_0000,
                0b1000_0000,
                0b1000_0000,
                0b1000_0000,
                0b0000_0000,
            ])
            .unwrap()
            .0,
            1 << 57
        );
    }
}
