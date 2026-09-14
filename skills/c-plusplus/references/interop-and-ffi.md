---
semantic_id: "oKqzRK97wTqxksITrGG7YfQpl9ZUIAAG"
related_ids:
  - "IQ45VK5BgTq3ssTGrmMbZ_wloZxQQAAI"
  - "KYoBAO7rixqWMsoCrGGfYbAvrZxIMAAP"
---
# Interop: C, Objective-C++, Python, and the ABI

Source:

- https://en.cppreference.com/w/cpp/language/language_linkage (`extern "C"`)
- https://itanium-cxx-abi.github.io/cxx-abi/abi.html (the Itanium C++ ABI)
- https://pybind11.readthedocs.io/
- https://nanobind.readthedocs.io/
- https://docs.python.org/3/extending/extending.html
- https://doc.rust-lang.org/nomicon/ffi.html / https://cxx.rs/

## 1. `extern "C"` and the C boundary

C++ mangles names (to encode overloads, namespaces, templates); C does not.
`extern "C"` turns off mangling and selects the C calling convention.

```cpp
// mylib.h — consumable from both C and C++
#ifdef __cplusplus
extern "C" {
#endif

typedef struct Engine Engine;                 // opaque handle
Engine*  engine_create(const char* config);
int      engine_run(Engine* e, const uint8_t* data, size_t len);
void     engine_destroy(Engine* e);
const char* engine_last_error(void);          // errors as codes/strings, never exceptions

#ifdef __cplusplus
}
#endif
```

```cpp
// mylib.cpp — C++ inside, C surface outside
extern "C" Engine* engine_create(const char* config) noexcept {
    try { return reinterpret_cast<Engine*>(new EngineImpl{config}); }
    catch (const std::exception& e) { set_last_error(e.what()); return nullptr; }
    catch (...) { set_last_error("unknown"); return nullptr; }
}
```

Rules for a C-compatible surface:

- **Never let an exception cross.** Catch everything at the boundary; unwinding
  through C frames is UB. Mark boundary functions `noexcept`.
- Only pass C-layout types: scalars, pointers, and `struct`s that are
  **standard-layout** (`static_assert(std::is_standard_layout_v<T>)`). No
  `std::string`, `std::vector`, references, or templates in the signature.
- Opaque pointers for C++ objects; a matching `destroy` for every `create`.
- `extern "C"` applies to functions, not to overloads — you can have only one
  function of a given name.
- Document ownership of every pointer explicitly; the type system can't.
- A C++ `struct` with virtual functions has a vptr as its first member and is not
  C-compatible.

Calling **into** C from C++ needs nothing special beyond the header being
`extern "C"`-wrapped (system headers already are).

## 2. ABI reality

There is **no stable C++ ABI**. Consequences:

- Objects compiled by different compilers (or MSVC debug vs release CRT, or
  libstdc++ vs libc++) generally cannot be linked.
- `std::string`/`std::vector` layouts differ across standard libraries; passing
  them across a shared-library boundary requires both sides built identically.
- libstdc++'s dual ABI: undefined references naming `__cxx11::basic_string` mean
  a `_GLIBCXX_USE_CXX11_ABI` mismatch.
- Adding a virtual function, changing member order, or changing a class's size
  breaks binary compatibility with existing callers even with the same compiler.

If you ship a library for third parties: **expose a C ABI**, or ship source, or
pin the exact toolchain. PIMPL plus a C surface is the standard shape for a
long-lived binary interface.

Symbol visibility on ELF/Mach-O — cuts load time, shrinks the binary, and stops
accidental ABI promises:

```cmake
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)
```

```cpp
#define API __attribute__((visibility("default")))     // or __declspec(dllexport) on MSVC
extern "C" API int engine_run(...);
```

Inspecting symbols: `nm -C lib.a`, `nm -D --defined-only lib.so`,
`c++filt _ZN4proj6WidgetC1Ev`, `objdump -T`, `dumpbin /EXPORTS` on Windows.

## 3. Python bindings

**nanobind** for new work (smaller, faster to compile, ~4× smaller binaries;
requires C++17 and Python 3.8+). **pybind11** where the ecosystem or an older
toolchain demands it. Both have essentially the same API.

```cpp
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
namespace nb = nanobind;

NB_MODULE(myext, m) {
    m.def("add", &add, "a"_a, "b"_a = 0, "Add two numbers");

    nb::class_<Engine>(m, "Engine")
        .def(nb::init<std::string>())
        .def("run", &Engine::run, nb::call_guard<nb::gil_scoped_release>())
        .def_prop_ro("size", &Engine::size)
        .def("__repr__", [](const Engine& e){ return std::format("<Engine {}>", e.name()); });
}
```

Key points:

- **Release the GIL** around anything long-running (`gil_scoped_release` /
  `nb::call_guard<>`), or you serialize the caller's whole interpreter.
- Crossing the boundary costs ~100 ns–1 µs per call. **Batch**: pass arrays, not
  scalars in a loop. This is the single biggest performance factor.
- Zero-copy numpy: `nb::ndarray<float, nb::shape<-1, 3>, nb::c_contig>` (or
  `py::array_t` in pybind11) views the buffer without copying — mind the
  lifetime of the owning object.
- Exceptions translate automatically (`std::runtime_error` → `RuntimeError`);
  register custom ones with `nb::register_exception_translator`.
- Build with **scikit-build-core** (CMake + modern Python packaging) rather than
  hand-rolled `setup.py`.

Alternatives: **Cython** (when the glue itself is the logic), **ctypes/cffi**
(against a C ABI, no build step), **SWIG** (many target languages, generated
code is unpleasant).

## 4. Objective-C++ (Apple platforms)

A `.mm` file compiles both languages in one TU — the standard bridge between a
C++ engine and Cocoa/Metal.

```objc
// Renderer.mm
#import <Metal/Metal.h>
#include "engine/Scene.hpp"

@implementation Renderer {
    std::unique_ptr<Scene> _scene;         // C++ members in an ObjC class: legal in .mm
    id<MTLDevice> _device;
}
- (void)draw {
    _scene->update();
    [_encoder drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:_scene->count()];
}
@end
```

- ARC manages ObjC objects; C++ destructors manage C++ ones. An ObjC object
  stored in a C++ struct needs `__strong`/`__bridge` care, and a C++ object
  owned by an ObjC class is destroyed in `dealloc` — which ARC calls for you if
  the member is a value or `unique_ptr`.
- ObjC exceptions and C++ exceptions are separate mechanisms; `@try` does not
  catch `throw`.
- Keep the `.mm` layer thin: platform glue only, logic in portable `.cpp`.
- Swift ↔ C++ interop (Swift 5.9+) is real but still sharp-edged; a C or
  Objective-C shim remains the reliable path for anything nontrivial.

## 5. Rust interop

- **cxx** (cxx.rs) — safe, bidirectional, generates the glue from a shared
  `#[cxx::bridge]` declaration. Handles `std::string`/`String`,
  `std::unique_ptr`, and `&[T]`/`rust::Slice`. The default choice.
- **cbindgen** (Rust → C header) / **bindgen** (C header → Rust) for a plain C
  ABI in either direction.
- **autocxx** for consuming large existing C++ APIs from Rust; ambitious, and
  rougher.

Same constraints as the C boundary: no exceptions across (cxx converts them to
`Result`), no unwinding through `extern "C"`, and explicit ownership.

## 6. WebAssembly

Emscripten (`emcc`) compiles C++ to wasm with `embind` or `WASM_EXPORTS` for the
JS boundary; exceptions and threads need explicit flags (`-fexceptions` /
`-pthread` + COOP/COEP headers) and cost size and speed. `wasi-sdk` for
non-browser wasm.

## Gotchas

- An exception escaping an `extern "C"` function is UB. `noexcept` at least turns
  it into a clean `terminate` instead of corruption.
- `extern "C"` does not disable C++ features _inside_ the function — only the
  linkage of its name.
- Passing `std::string`/`std::vector` across a shared-library boundary requires
  identical compiler, standard library, and flags on both sides.
- Mixing MSVC debug and release CRTs corrupts the heap: `new` in one CRT, `delete`
  in the other.
- Every `create` needs a matching `destroy` **in the same library** — a C caller
  must not `free()` memory that C++ `new`ed.
- `reinterpret_cast` between an opaque handle and the implementation type is fine
  only if it's the same type both ways; casting through a base with multiple
  inheritance shifts the pointer.
- Python: forgetting to release the GIL turns a "parallel" extension into a
  sequential one, silently.
- Per-call FFI overhead dominates fine-grained APIs. Design for batches.
- Static initialization in a shared library runs at `dlopen`; ordering across
  libraries is unspecified, and a global constructor that calls back into the
  loading program will bite.
