use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pyfunction]
fn varint(buffer: Vec<u8>) -> PyResult<u64> {
    println!("Hello {buffer:?}");
    return Ok(buffer[0] as u64)
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
}