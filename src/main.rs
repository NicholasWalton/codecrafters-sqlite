use pyo3::prelude::*;

use codecrafters_sqlite::foo;

fn main() -> PyResult<()> {
    pyo3::append_to_inittab!(foo);
    Python::with_gil(|py| Python::run_bound(py, "import foo; foo.add_one(6)", None, None))
}