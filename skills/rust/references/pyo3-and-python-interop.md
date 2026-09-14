---
semantic_id: "XIC5jDd4YwTxExOTLKWzEXA5d9I-IAAB"
related_ids:
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
  - "urRuzaZ578T7mxDgNIRyUfgpM1BJIAAE"
---
# PyO3 and Python interop

Source:

- <https://pyo3.rs/> (the PyO3 user guide, current release)
- <https://pyo3.rs/latest/migration> (the per-release breaking-change log: read this first)
- <https://pyo3.rs/latest/parallelism> (releasing the GIL, free-threaded builds)
- <https://www.maturin.rs/> (building and publishing wheels)
- <https://docs.rs/numpy/latest/numpy/> (ndarray interop)

## 1. What it is for

PyO3 lets you write a native Python extension module in Rust, or embed Python in a Rust
program. The usual reason is a hot loop: keep the ergonomics and ecosystem of Python at the
edges, move the inner loop into Rust, and release the GIL while it runs so real threads
work.

The alternative approaches, briefly: a plain `cdylib` with `extern "C"` plus `ctypes`/`cffi`
on the Python side (no PyO3 dependency, no Python objects, painful for anything structured),
or `uniffi` if you also need Kotlin and Swift bindings from the same core.

## 2. Project shape

```toml
# Cargo.toml
[lib]
name = "myext"
crate-type = ["cdylib"]          # "rlib" too if Rust code also depends on it

[dependencies]
pyo3 = { version = "0.2x", features = ["extension-module", "abi3-py39"] }
```

```toml
# pyproject.toml
[build-system]
requires = ["maturin>=1.7,<2.0"]
build-backend = "maturin"

[project]
name = "myext"
requires-python = ">=3.9"
```

```bash
pip install maturin
maturin develop --release     # build and install into the active venv
maturin build --release       # produce a wheel in target/wheels/
```

`maturin develop` requires an activated virtualenv and is the entire dev loop. For a mixed
project (Python package with a Rust core), put the Python in `python/myext/` and set
`python-source = "python"` under `[tool.maturin]`; the compiled module lands beside it.

`abi3-pyXY` builds one wheel that works on that Python version and every later one, which
cuts your CI matrix from N builds to 1. The cost is losing a few APIs that are not in the
stable ABI. Without it, you build per Python version (`cibuildwheel` or maturin's GitHub
Action automates this).

## 3. The core API

```rust
use pyo3::prelude::*;

#[pyfunction]
fn count_tokens(text: &str) -> usize { text.split_whitespace().count() }

#[pyfunction]
#[pyo3(signature = (data, *, workers = 4))]         // keyword-only arg with a default
fn process(data: Vec<f64>, workers: usize) -> PyResult<Vec<f64>> {
    if workers == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err("workers must be > 0"));
    }
    Ok(data.into_iter().map(|x| x * 2.0).collect())
}

#[pyclass]
struct Index { #[pyo3(get, set)] size: usize, inner: Vec<u32> }

#[pymethods]
impl Index {
    #[new]
    fn new(size: usize) -> Self { Self { size, inner: vec![0; size] } }
    fn lookup(&self, k: u32) -> Option<usize> { self.inner.iter().position(|&v| v == k) }
    fn __len__(&self) -> usize { self.inner.len() }
    fn __repr__(&self) -> String { format!("<Index size={}>", self.size) }
}

#[pymodule]
fn myext(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(count_tokens, m)?)?;
    m.add_function(wrap_pyfunction!(process, m)?)?;
    m.add_class::<Index>()?;
    Ok(())
}
```

**The `#[pymodule]` function name must equal the module name Python imports**, which must
equal `[lib] name`. A mismatch is `ImportError: dynamic module does not define module export
function`.

Conversions happen automatically for the obvious types: `String`/`&str` to `str`,
`Vec<T>`/`HashMap<K,V>` to `list`/`dict`, `Option<T>` to `None`-or-value, numeric types,
`bool`, `PyResult` to an exception. Implement `FromPyObject` for custom input types and
`IntoPyObject` for custom returns (older `IntoPy`/`ToPyObject` are deprecated in current
releases).

## 4. The GIL, `Python<'py>`, and `Bound`

Any access to a Python object requires holding the GIL, and the token proving you hold it is
`Python<'py>`. Modern PyO3 represents every Python object as `Bound<'py, T>`: a reference
tied to that token. `Py<T>` is the GIL-independent owned form you store in a struct or send
across threads, converted back with `.bind(py)`.

The older "GIL Refs" API (`&PyAny`, `Python::acquire_gil`) has been removed; if you find
that shape in a snippet, it predates the current release line.

The performance-relevant call is `allow_threads`, which drops the GIL around pure-Rust work
so other Python threads can run:

```rust
#[pyfunction]
fn heavy(py: Python<'_>, data: Vec<f64>) -> Vec<f64> {
    py.allow_threads(|| {
        use rayon::prelude::*;
        data.par_iter().map(|x| expensive(*x)).collect()
    })
}
```

Inside `allow_threads` you cannot touch any Python object, and the closure must be `Send`,
both of which the type system enforces. Any CPU-bound function taking more than a
millisecond should be wrapped this way, and `rayon` inside it is where the actual win comes
from.

Python 3.13+ free-threaded builds (no GIL) are supported by recent PyO3 via the
`Py_GIL_DISABLED` path, but extensions must be explicitly marked as supporting it and any
`unsafe` shared state assumptions get much sharper. Verify against the guide before
claiming support.

## 5. NumPy and zero-copy

```rust
use numpy::{PyArray1, PyReadonlyArray1, PyArrayMethods};

#[pyfunction]
fn normalise<'py>(py: Python<'py>, a: PyReadonlyArray1<'py, f64>) -> Bound<'py, PyArray1<f64>> {
    let view = a.as_array();                       // ndarray::ArrayView1, borrows numpy memory
    let max = view.iter().cloned().fold(f64::MIN, f64::max);
    let out: Vec<f64> = view.iter().map(|x| x / max).collect();
    PyArray1::from_vec(py, out)
}
```

`PyReadonlyArray` borrows the numpy buffer with no copy, which is the point: passing a
100 MB array costs nothing. It fails cleanly if the array is not contiguous or has the wrong
dtype, so the Python side may need `np.ascontiguousarray(x, dtype=np.float64)`.

`numpy` crate versions are pinned to specific `pyo3` and `ndarray` versions. Mismatches
produce trait-resolution errors that look like PyO3 bugs and are dependency-version bugs.

## 6. Performance shape

The boundary crossing is roughly a microsecond, so:

- **Batch.** One call handling 10,000 items beats 10,000 calls handling one, by orders of
  magnitude. A Rust function called from inside a Python `for` loop can easily be slower
  than pure Python.
- Prefer passing numpy arrays or `bytes` over lists of Python objects; converting a
  `list[float]` of a million elements to `Vec<f64>` allocates and touches a million
  `PyObject`s.
- Return `bytes`/arrays rather than large nested structures.
- Release the GIL for anything non-trivial, or you have built a fast function that still
  serialises your users' threads.

## Gotchas

- **PyO3 makes breaking API changes every minor release.** Pin the version, and read
  `pyo3.rs/latest/migration` before bumping. Snippets from a blog post two releases old will
  not compile, and the errors do not say "this API is from an older version".
- The `extension-module` feature must be **off** when building tests or a binary that embeds
  Python, and **on** when building a wheel, because it stops linking libpython. The symptom
  of getting it wrong is a linker error about `_Py_...` symbols at test time. The usual fix
  is an optional feature that maturin enables and `cargo test` does not.
- Module name, `[lib] name`, and the `#[pymodule]` function name must all match, or the
  import fails with a message about the export function rather than about the name.
- `#[pyclass]` types must be `Send` (use `#[pyclass(unsendable)]` to opt out, which then
  panics if touched from another thread). A `Rc` or a raw pointer inside a `#[pyclass]` is a
  compile error for a good reason.
- A Rust `panic!` crosses into Python as `pyo3_runtime.PanicException`, which is not an
  `Exception` subclass in the way users expect and will not be caught by `except Exception`.
  Convert errors to `PyErr` deliberately; do not let panics escape.
- Deadlock: holding the GIL while blocking on a lock that another thread needs the GIL to
  release. Anything blocking goes inside `allow_threads`.
- `maturin develop` installs into the **active** virtualenv; run it without one and it either
  errors or silently targets the wrong interpreter. `maturin develop` also defaults to a
  debug build, which is 10x to 100x slower: always `--release` when benchmarking.
- Type stubs (`.pyi`) are not generated. Without them the extension has no autocomplete or
  type checking on the Python side; write them by hand or use `pyo3-stub-gen`.
- `#[pyo3(signature = ...)]` is required to express keyword-only arguments, defaults, and
  `*args`/`**kwargs`. Without it every parameter is positional-or-keyword with no default,
  and Python callers get confusing `TypeError`s.
- Returning a reference into Rust-owned data is not possible across the boundary; Python
  gets an owned object or a `#[pyclass]` handle, never a borrow.
- `abi3` wheels cannot use APIs outside the stable ABI, and some PyO3 features (certain
  `#[pyclass]` options) are unavailable under it. The build error appears only when the
  feature is enabled, not when you first add the attribute.
