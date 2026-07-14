---
topic_id: "v2:OJND"
topic_path: "rust-arkit/rust-fundamentals"
semantic_id: "_LDnGSZx7kR7lwyEKpe_U7lKEUTsUAAM"
related_ids:
  - "vKDvGWJf70R7BhSoKrHZWYhJ0XTIcAAA"
  - "urRuzaZ578T7mxDgNIRyUfgpM1BJIAAE"
---
# Unsafe Rust and FFI

Source:

- https://doc.rust-lang.org/nomicon/ (The Rustonomicon: the unsafe-Rust book)
- https://doc.rust-lang.org/std/ffi/ (CString, CStr, c_int and friends)
- https://github.com/rust-lang/miri (Miri, the UB interpreter)
- https://rust-lang.github.io/rust-bindgen/ and https://github.com/mozilla/cbindgen

## 1. What `unsafe` actually permits

Inside an `unsafe` block you gain exactly five superpowers:

1. Dereference raw pointers (`*const T`, `*mut T`)
2. Call `unsafe` functions (including `extern` functions)
3. Implement `unsafe` traits (`Send`, `Sync`, ...)
4. Access or modify a mutable `static`
5. Access fields of a `union`

That is the whole list. `unsafe` does **not** turn off the borrow checker, type checking, or any other analysis; references are still checked, moves are still moves. It only unlocks operations the compiler cannot verify, and shifts the proof obligation to you. Undefined behavior (dangling pointers, aliasing violations, data races, invalid values like a `bool` holding 3) remains just as illegal inside `unsafe`; the compiler simply trusts you.

## 2. Safety invariants and `// SAFETY` comments

Every `unsafe fn` documents its preconditions in a `# Safety` doc section; every `unsafe { }` block carries a `// SAFETY:` comment stating why the preconditions hold **here**:

```rust
// SAFETY: `idx < self.len` was checked above, and `self.ptr` is valid
// for `self.len` elements by the struct invariant.
let val = unsafe { *self.ptr.add(idx) };
```

In edition 2024, the body of an `unsafe fn` is no longer an implicit unsafe block (`unsafe_op_in_unsafe_fn` warns): you write explicit `unsafe { }` blocks inside, each with its own justification.

## 3. Raw pointers

```rust
let mut x = 5_i32;
let p: *mut i32 = &raw mut x;   // &raw (stable 1.82) takes a pointer WITHOUT creating a reference
unsafe { *p += 1; }
```

Raw pointers may be null, dangling, unaligned, and freely aliased; none of that is UB until you dereference (or otherwise rely on validity). Prefer `&raw const` / `&raw mut` (or `addr_of!`) over `&x as *const _` when the place might be uninitialized or unaligned, because creating an intermediate **reference** to invalid data is instant UB.

## 4. extern "C", both directions

Calling C from Rust (edition 2024 requires `unsafe extern`):

```rust
unsafe extern "C" {
    fn strlen(s: *const core::ffi::c_char) -> usize;
}
let n = unsafe { strlen(c"hello".as_ptr()) };   // c"" literals are &CStr
```

Exposing Rust to C: `#[unsafe(no_mangle)]` (the edition-2024 spelling; bare `#[no_mangle]` is an error there) plus `extern "C"`, and `#[repr(C)]` on any struct that crosses the boundary so field order/layout matches C:

```rust
#[repr(C)]
pub struct Point { pub x: f64, pub y: f64 }

#[unsafe(no_mangle)]
pub extern "C" fn point_len(p: Point) -> f64 {
    (p.x * p.x + p.y * p.y).sqrt()
}
```

Without `#[repr(C)]`, Rust's default layout is unspecified and may reorder fields.

## 5. Building a C-callable cdylib

```toml
[lib]
crate-type = ["cdylib"]      # .so / .dylib / .dll with C ABI exports
```

```bash
cargo build --release        # target/release/libmycrate.dylib
```

Export `#[unsafe(no_mangle)] pub extern "C"` functions, keep every crossing type `#[repr(C)]` or a raw pointer, and ship a header (see cbindgen).

**bindgen** (C to Rust): point it at a C header and it generates the Rust `extern` declarations, `#[repr(C)]` structs, and constants automatically, usually from `build.rs`. It is the standard way to consume a nontrivial C library; you then wrap the raw `-sys` bindings in a safe Rust API by hand.

**cbindgen** (Rust to C): walks your crate and emits a C (or C++) header for your `extern "C"` exports, so C callers get real prototypes instead of hand-maintained ones. Run it in `build.rs` or CI so the header can never drift from the code.

## 6. Strings across the boundary

C strings are nul-terminated; Rust strings are length + UTF-8. `CString` (owned) and `CStr` (borrowed) are the bridge:

```rust
use std::ffi::{CString, CStr};

let s = CString::new("hello")?;          // fails if the input contains interior \0
unsafe { c_takes_string(s.as_ptr()); }   // s must OUTLIVE the call: don't inline-temp it

// Handing ownership to C and back:
let raw = CString::new("data")?.into_raw();   // C side holds it...
let back = unsafe { CString::from_raw(raw) }; // ...and must return it HERE to free it
```

Rule: memory is freed by whoever allocated it. C must never `free()` a `CString`; Rust must never drop memory that C's allocator owns (wrap it and call the library's own `_free` function).

## 7. Miri: the UB checker

```bash
rustup +nightly component add miri
cargo +nightly miri test
```

Miri interprets your code and catches UB dynamically: out-of-bounds, use-after-free, invalid values, memory leaks, and aliasing-model violations (Stacked/Tree Borrows) that no sanitizer sees. It only checks code paths your tests execute, and it cannot run through real FFI calls, but it is the closest thing to a proof your unsafe code is sound. Run it on any crate with nontrivial `unsafe`.

## 8. When to just use a crate

- `libloading`: load shared libraries and symbols at runtime (plugins), instead of hand-rolled `dlopen`.
- `pyo3`: Python bindings both directions, with `maturin` for building wheels.
- `napi-rs` (or `neon`): Node.js native modules.
- `cxx`: safe, verified bridges to C++ (which raw `extern "C"` cannot express).

If a maintained binding crate exists for your target, the hand-written `extern` block is usually the wrong move.

## Gotchas

- Creating a `&T`/`&mut T` to uninitialized, dangling, or misaligned memory is UB **even if never dereferenced**. Use `MaybeUninit<T>`, raw pointers, and `&raw` until the value is fully initialized.
- Edition 2024 spellings trip people up: `unsafe extern "C" { }` for blocks, `#[unsafe(no_mangle)]` / `#[unsafe(export_name = ...)]` for attributes. The old bare forms are hard errors on the new edition.
- `CString::new` returns `Err` on interior nul bytes: don't `unwrap` on untrusted input.
- `CString::new(...)?.as_ptr()` as a temporary is a classic dangling pointer: the `CString` drops at the end of the statement. Bind it to a variable that outlives the call.
- Panicking across an `extern "C"` boundary used to be UB; now it **aborts** the process. Use `extern "C-unwind"` if unwinding must cross, or catch panics with `std::panic::catch_unwind` at the boundary.
- `unsafe` does not disable borrow checking. If the compiler rejects your aliasing, raw pointers may express it, but the aliasing rules still apply semantically and Miri will call it UB.
- Use `core::ffi` type aliases (`c_int`, `c_char`, `c_long`) in signatures, not `i32`/`i8`/`i64`: C type widths vary by platform (`c_char` signedness varies too, e.g. unsigned on aarch64 Linux).
- `mem::transmute` checks only size, not validity: transmuting 3 to `bool`, an invalid discriminant to an enum, or non-UTF-8 to `str` is instant UB.
- A `union` field read is unchecked reinterpretation; unlike C, reading a different field than last written is fine ONLY if the bytes are valid for the read type.
