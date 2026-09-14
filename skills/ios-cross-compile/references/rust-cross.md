---
semantic_id: "icW7MvLeG0v8iLsqdhRmM5gX1VGYsAAD"
related_ids:
  - "iQUjMvDaH0u8mHtAbTTuKqp3zVNIkAAG"
  - "l0Q7NvD6G06wmpMOenx2OaA3wPccoAAM"
---
# Rust + CMake cross-compiling

Provenance: verified empirically during a real iOS port (2026) — the mixed archive was
proven at the object level and the fix verified by re-counting objects per platform.

## 1. The shared-triple bug

CMake glue that builds Rust crates typically derives one target triple from
`rustc -vV`'s **host** line, caches it, and uses it everywhere. That is wrong the moment
the build has both roles:

- **host tools** (`cargo build` binaries executed during the build) — must be the
  _host_ triple;
- **static libraries linked into the product** (`import_rust_crate`-style, `ar`-merged
  into C++ archives) — must be the _target_ triple.

With one shared triple, a cross build produces **host-platform Rust archives linked
into target-platform libraries**. And here is the nasty part:

> **`ar` does not check platform.** The merge succeeds. The mixed archive "links
> successfully" as far as the library step is concerned.

In the observed case, the flagship library archive contained 1305 iOS C++ objects and
631 **macOS** Rust objects, spliced together by a POST_BUILD `ar` merge, with zero
diagnostics. Nothing fails until the final executable link — or worse, until runtime.

## 2. The fix: split host and target triples

- Compute `RUST_HOST_TRIPLE` from `rustc -vV`'s host line; compute
  `RUST_TARGET_TRIPLE` from the _CMake target platform_, and pass the right one per
  crate role (a `HOST_TOOL` option on the crate function is a clean seam).
- Host-tool builds must also **not** receive the cross environment: strip the cross
  `CC_*`/`CXX_*`/linker/`AR_*`/`SDKROOT` variables for them, or cargo's build scripts
  compile for the wrong world.
- **Unknown target platform → hard configure error**, never a silent host fallback.

### Apple triple mapping

| CMake target          | Rust triple             |
| --------------------- | ----------------------- |
| iOS device            | `aarch64-apple-ios`     |
| iOS simulator (arm64) | `aarch64-apple-ios-sim` |
| macOS arm64           | `aarch64-apple-darwin`  |

Device vs simulator is distinguished **only by the sysroot** — `CMAKE_OSX_SYSROOT`
matching `[Ss]imulator` means `-sim`. `CMAKE_SYSTEM_NAME` is `iOS` for both.

The target's std must be installed: `rustup target add aarch64-apple-ios` (and
`aarch64-apple-ios-sim` for the simulator). Without it the split triple has nothing to
compile against.

## 3. Verifying an archive is really single-platform

Trust nothing; count objects. `vtool -show-build` prints the platform load command per
object.

```sh
cd $(mktemp -d)
ar x /path/to/libfoo.a
for o in *.o; do vtool -show-build "$o" | head -4; done
```

Two traps in the verification itself:

- **rustc and clang emit different load commands for the same platform.** Modern clang
  emits `LC_BUILD_VERSION` with `platform IOS`; rustc emits the older
  `LC_VERSION_MIN_IPHONEOS`. A naive `grep "platform"` therefore **undercounts** —
  Rust iOS objects have no `platform` line at all. Count both forms:

  ```sh
  vtool -show-build "$o" | grep -E 'platform|LC_VERSION_MIN'
  ```

  (`platform IOSSIMULATOR` is the simulator; macOS is `platform MACOS` /
  `LC_VERSION_MIN_MACOSX`.)

- **Fat archives need `lipo -thin arm64` before `ar x`** — `ar` can't extract from a
  multi-arch archive directly. And not every member is named `*.o`: ICU's archives use
  a **`.ao` extension** for their assembly-data objects, so glob accordingly.

A healthy result reads like "1936/1936 iOS objects": every object accounted for, zero
from the other platform.

## 4. Gotchas

- Configure can pass and the build get far along with this bug present — the mixed
  archive is created _silently at library link time_. Check archives even when the
  build is green.
- `cargo` must be on `PATH` at configure time for triple detection; a broken rustup
  shim (dangling `~/.cargo/bin` symlinks) fails in confusing ways — invoke the
  toolchain's real `bin` directory if in doubt.
- The link error, when you finally get one, names the _executable_ being linked
  ("building for iOS, but linking in object file built for macOS"), not the archive
  merge that caused it.
