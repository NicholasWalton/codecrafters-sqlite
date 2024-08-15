use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pyfunction]
fn varint(buffer: Vec<u8>) -> PyResult<u64> {
    println!("Hello {buffer:?}");
    let huffman_length = 9;
    let mut unsigned = 0u64;
    for byte_index in 0..huffman_length - 1 { // zero or more bytes which have the high-order bit set
        unsigned = (unsigned) << 7 + _lower7(buffer.get(byte_index).unwrap()); // The lower seven bits of each of the first n-1 byte
        if 0 == _high_bit(buffer.get(byte_index).unwrap()) {  // including a single end byte with the high-order bit clear
            break;
        }
        if byte_index == huffman_length {
            unsigned = (unsigned << 8) + buffer[byte_index + 1] as u64;  // or all 8 bits of the nth byte
        }
    }
    let huffman_bits = 7 * huffman_length + 1;
    let sign_bit = 1 << (huffman_bits - 1);
    if (unsigned & sign_bit) != 0 {
        Ok(unsigned - (sign_bit << 1))
    } else {
        Ok(unsigned)
    }
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
        assert_eq!(varint(vec![0]).unwrap(), 0u64);
    }

    #[test]
    fn one() {
        assert_eq!(varint(vec![1]).unwrap(), 1u64);
    }

    #[test]
    fn eight_bits() {
        assert_eq!(varint(vec![0b1000_0001, 0b0000_0000]).unwrap(), 128u64);
    }
}