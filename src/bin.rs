use std::path::Path;

use ::codecrafters_sqlite::decode_varint;
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyList};

// extern crate codecrafters_sqlite;

// use codecrafters_sqlite;
// #[pyfunction]
// pub fn decode_varint(buffer: Vec<u8>) -> PyResult<(i64, usize)> {
//     decode_varint_inner(&buffer)
// }
//
// #[pymodule]
// fn foo(m: &Bound<'_, PyModule>) -> PyResult<()> {
//     m.add_function(wrap_pyfunction!(decode_varint, m)?)?;
//     Ok(())
// }

// #[pymodule(name = "codecrafters_sqlite")]
// mod shim {
//     use super::*;
//     use pyo3::prelude::*;
use ::codecrafters_sqlite::_lowlevel;
//
//     #[pymodule]
//     mod _lowlevel {
//         use ::codecrafters_sqlite::decode_varint_inner;
//         use super::*;
//         use pyo3::PyResult;
//         // use crate::codecrafters_sqlite::decode_varint_inner;
//
//         #[pyfunction]
//         pub fn decode_varint(buffer: Vec<u8>) -> PyResult<(i64, usize)> {
//             decode_varint_inner(&buffer)
//         }
//     }
// }

#[pymodule(name = "rust_codecrafters_sqlite")]
fn bar(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    let child_module = PyModule::new_bound(parent_module.py(), "_lowlevel")?;
    child_module.add_function(wrap_pyfunction!(decode_varint, &child_module)?)?;
    parent_module.add_submodule(&child_module)
}

fn main() -> PyResult<()> {
    // let dict = test_varint_performance.dict();
    // for item in dict.items() {
    //     dbg!(&item);
    // }

    // let py_foo = include_str!(concat!(
    // env!("CARGO_MANIFEST_DIR"),
    // "/test_varint_performance.py"
    // ));
    // let codecrafters_py = concat!(env!("CARGO_MANIFEST_DIR"), "/python/codecrafters_py");
    // let python = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/python/codecrafters_py"));
    // let foo;
    // codecrafters_sqlite(foo);

    let project_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("python");
    // let path = project_dir.join("tests/test_varint_performance.py");
    // let py_app = std::fs::read_to_string(&path).unwrap();
    pyo3::append_to_inittab!(bar);

    Python::with_gil(|py| {
        // let from_python = Python::with_gil(|py| -> PyResult<Py<PyAny>> {
        let syspath = py
            .import_bound("sys")
            .unwrap()
            .getattr("path")
            .unwrap()
            .downcast_into::<PyList>()
            .unwrap();
        syspath.insert(0, &project_dir).unwrap();
        // let pyo3_rust_module = PyModule::import_bound(py, "codecrafters_sqlite").expect("Couldn't import bound");
        // syspath.insert(1, &pyo3_rust_module).expect("Couldn't insert codecrafters_sqlite into syspath");
        //     // let python_module = PyModule::import_bound(py, "codecrafters_py").expect("Couldn't import bound");
        //     // syspath.insert(2, &python_module).expect("Couldn't insert codecrafters_py into syspath");
        //     // PyModule::from_code_bound(py, codecrafters_py, "codecrafters_py.py", "codecrafters_py")?;
        //
        //
        //     let app: Py<PyAny> = PyModule::from_code_bound(py, py_app.as_str(), "", "").expect("Couldn't do from code_bound")
        //         .getattr("main").unwrap()
        //         .into();
        //     app.call0(py)
        // });
        // println!("py: {}", from_python.expect("Couldn't run"));

        Python::run_bound(
            py,
            "
import codecrafters_sqlite
import rust_codecrafters_sqlite
print(dir(codecrafters_sqlite))
print(dir(rust_codecrafters_sqlite))
",
            None,
            None,
        )?;
        Python::run_bound(
            py,
            r#"
import pytest
pytest.main(args=["python/tests/test_varint_performance.py","--durations=0"])
"#,
            None,
            None,
        )
    })

    // let result = dbg!(test_varint_performance.dict()).getattr("main")?.call0()?;
    // println!("Result: {}", result);
    // let sys = py.import_bound("sys")?;
    // let version: String = sys.getattr("version")?.extract()?;
    //
    // let locals = [("os", py.import_bound("os")?)].
    //     into_py_dict_bound(py);
    // let code = "os.getenv('USER') or os.getenv('USERNAME') or 'Unknown'";
    // let user: String = py.eval_bound(code, None, Some(&locals))?.extract()?;
    //
    // println!("Hello {}, I'm Python {}", user, version);
    // Ok(())
}
