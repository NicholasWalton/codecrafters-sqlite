use std::path::Path;

use codecrafters_sqlite::_lowlevel;
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::wrap_pymodule;

#[pymodule]
fn rust_codecrafters_sqlite(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_wrapped(wrap_pymodule!(_lowlevel))
}

fn main() -> PyResult<()> {
    pyo3::append_to_inittab!(rust_codecrafters_sqlite);

    Python::with_gil(|py| {
        let project_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("python");
        let syspath = py
            .import_bound("sys")?
            .getattr("path")?
            .downcast_into::<PyList>()?;
        syspath.insert(0, &project_dir)?;
        Python::run_bound(
            py,
            r#"
import codecrafters_sqlite
import rust_codecrafters_sqlite
import pytest
pytest.main(args=["python/tests/test_varint_performance.py", "--durations=0"])
"#,
            None,
            None,
        )
    })
}
