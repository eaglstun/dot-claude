---
semantic_id: "iQUjMvDaH0u8mHtAbTTuKqp3zVNIkAAG"
related_ids:
  - "icW7MvLeG0v8iLsqdhRmM5gX1VGYsAAD"
  - "mcWpM1Db01u9rRpgUjfkI4RXzleFkAAJ"
---
# Host tools when cross-compiling

Provenance: verified empirically during a real iOS port of a large C++/CMake codebase
(2026). No upstream docs cover this pattern end to end; the LLVM shape referenced below
is `LLVM_NATIVE_TOOL_DIR` in LLVM's own build.

## 1. The problem

Large C++ projects often compile some of their code generators — layout generators,
bytecode emitters, table builders — as `add_executable` targets that later steps run via
`add_custom_command`. CMake has **no built-in notion of a host tool**: when
cross-compiling, those executables are built for the _target_ and then _executed on the
build machine_.

On iOS the symptom is the kernel SIGKILLing the binary — the custom command fails with
**exit code 137** and no useful message. On other targets it's typically an
`exec format error`. Either way the generator "built fine" and the failure lands on
whatever consumes its output.

Python/script generators are immune — they run on the host interpreter regardless of
target. Only compiled generators have this problem, which is a good argument for keeping
generators as scripts where possible.

## 2. The two fix patterns

**a) Import from a separate native build directory** (LLVM's `LLVM_NATIVE_TOOL_DIR`
shape). Configure the project once natively, build only the tools there, and have the
cross build import them as `IMPORTED` executables from a cache variable like
`MYPROJ_HOST_TOOLS_DIR`. Simple, explicit, and the native build can be tiny — if the
tool only needs the project's foundation library, the host build may be a minute of
compiling (most of its configure cost being the package manager, which can reuse an
already-populated native dependency tree).

**b) An ExternalProject sub-build** — the cross configure itself spawns a nested native
CMake build for the tools. Self-contained, but slower to configure and harder to debug.

Pattern (a) is what worked in practice. Two configure commands instead of one, but each
is ordinary and inspectable:

```sh
cmake -S . -B build/host-tools -G Ninja <the usual native options>
cmake --build build/host-tools --target my_generator
cmake -S . -B build/ios ... -DMYPROJ_HOST_TOOLS_DIR=$PWD/build/host-tools
```

## 3. A worked wrapper: `add_host_executable()`

The call sites shouldn't care which world they're in, so wrap the split in one function.
The essential constraints, each learned the hard way:

- **`target_compile_definitions()` / `target_compile_options()` / etc. CANNOT be called
  on an IMPORTED target.** So the wrapper must take those as _arguments_ and apply them
  only in the native branch. Callers pass `COMPILE_DEFINITIONS ...` instead of making
  their own `target_*()` calls.
- **An IMPORTED executable cannot be a build-order dependency.** Custom commands must
  `DEPENDS` on the tool's _file path_ (export it from the wrapper, e.g.
  `${name}_HOST_PATH`), not name the target.
- **`CMAKE_EXECUTABLE_SUFFIX` describes the target**, but the tool belongs to the build
  machine — use `CMAKE_HOST_WIN32` to decide whether the imported path ends in `.exe`.
- **Hard-error, never silently fall back.** If cross-compiling and the host-tools dir is
  unset or missing the tool, `message(FATAL_ERROR ...)` with the exact commands to fix
  it. A silent fallback here produces a target-arch binary that dies at build time with
  exit 137 and no explanation.

Skeleton (trimmed from a working implementation):

```cmake
function(add_host_executable name)
    cmake_parse_arguments(PARSE_ARGV 1 ARG "" ""
        "LIBRARIES;COMPILE_DEFINITIONS;COMPILE_OPTIONS;LINK_OPTIONS")

    if (NOT CMAKE_CROSSCOMPILING)
        add_executable(${name} ${ARG_UNPARSED_ARGUMENTS})
        # ... target_link_libraries / target_compile_definitions from ARG_* ...
        set(${name}_HOST_PATH "$<TARGET_FILE:${name}>" PARENT_SCOPE)
        return()
    endif()

    if (NOT MYPROJ_HOST_TOOLS_DIR)
        message(FATAL_ERROR "Cross-compiling needs a native build for '${name}'. "
            "Configure one and pass -DMYPROJ_HOST_TOOLS_DIR=<dir>.")
    endif()
    if (CMAKE_HOST_WIN32)
        set(suffix ".exe")
    else()
        set(suffix "")
    endif()
    set(tool_path "${MYPROJ_HOST_TOOLS_DIR}/bin/${name}${suffix}")
    if (NOT EXISTS "${tool_path}")
        message(FATAL_ERROR "'${tool_path}' missing. Build it: "
            "cmake --build ${MYPROJ_HOST_TOOLS_DIR} --target ${name}")
    endif()
    add_executable(${name} IMPORTED GLOBAL)
    set_target_properties(${name} PROPERTIES IMPORTED_LOCATION "${tool_path}")
    set(${name}_HOST_PATH "${tool_path}" PARENT_SCOPE)
endfunction()
```

Note the deeper reason a C++ host tool can't just be "retargeted with a different
triple" the way a Rust binary can: it typically links the project's _own_ libraries,
which in the cross build exist only as target-arch archives. The native build is the
only place a host copy of those libraries exists.

## 4. The struct-layout rule

If the host tool emits **struct offsets, sizes, or memory layouts** consumed by
target code (interpreter layout tables, serialized headers), the host build must match
the target build in **every option that changes struct layout — sanitizers above all**
(ASan changes struct sizes, and code that keys constants off
`HAS_ADDRESS_SANITIZER`-style macros will drift). A mismatched pair produces silently
wrong layouts, not errors.

Verification that settles it: generate the artifact in both a native build and via the
imported host tool and diff them. In the port this came from, the generated layout file
was **byte-identical** between the two, which is the difference between "sound" and
"merely expedient".

## 5. Gotchas

- Rust host tools have the same disease with a different mechanism — a shared target
  triple rather than a shared toolchain. See [rust-cross.md](rust-cross.md).
- The host-tools gap usually affects **every** cross target, not just iOS (Android NDK
  builds of the same tree hit the identical shape) — a fix framed for all
  cross-compilation is more likely to be accepted upstream than an iOS-only one.
- Exit 137 = 128 + SIGKILL(9). If a build step dies with 137 on macOS while
  cross-compiling, check the architecture of the binary being executed before
  suspecting memory pressure.
