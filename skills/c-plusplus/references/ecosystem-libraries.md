---
semantic_id: "La4BRftpxbrzutYQqNBbYvA_yVRIUAAE"
related_ids:
  - "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
  - "L4oZQVJrxn7zOk4ErrUv6vQvi0zIYAAB"
---
# The library ecosystem: which one do I reach for

Source:

- https://github.com/fffaraz/awesome-cpp
- https://abseil.io/docs/cpp/
- https://www.boost.org/doc/libs/
- https://think-async.com/Asio/ (Asio)
- https://github.com/nlohmann/json / https://json.nlohmann.me/

The standard library covers containers, algorithms, strings, threads, and (since
C++20) formatting and ranges. Everything below is what people actually add.

## 1. General-purpose foundations

| Need                    | Library                                                                       | Notes                                                                                                |
| ----------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Google's std extensions | **Abseil**                                                                    | `flat_hash_map` (fast), `Span`, `StrCat`/`StrFormat`, `Cleanup`, `Status`, time. Live-at-head policy |
| Everything, mature      | **Boost**                                                                     | huge; use it à la carte. Many parts are now in std                                                   |
| LLVM's containers       | `llvm::SmallVector`, `DenseMap`, `StringRef`                                  | excellent, but drags in LLVM                                                                         |
| Fast hash maps          | `boost::unordered_flat_map`, `absl::flat_hash_map`, `ankerl::unordered_dense` | 2–5× `std::unordered_map`                                                                            |
| Small-buffer vectors    | `boost::container::small_vector`, `absl::InlinedVector`                       | avoids heap for small N                                                                              |
| Formatting              | **{fmt}**                                                                     | what `std::format` came from; use when `<format>` is unavailable                                     |
| Ranges beyond C++20     | **range-v3**                                                                  | still ahead of the standard                                                                          |

Boost parts still worth it in a C++20 world: `Asio`, `multi_index`,
`intrusive`, `graph`, `program_options` (though see CLI below), `Beast` (HTTP),
`interprocess`, `spirit`/`parser`, `unordered` (the flat maps), `stacktrace`,
`math`.

## 2. Serialization and data formats

| Format                        | Library                                                                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- |
| JSON, ergonomic               | **nlohmann/json** — `json j = {{"k", 1}};`, slow-ish but delightful                                  |
| JSON, fast                    | **simdjson** (parse-only, GB/s), **RapidJSON**, **glaze** (header-only, reflection-based, very fast) |
| Binary schema, cross-language | **Protobuf** (ubiquitous), **FlatBuffers** (zero-copy reads), **Cap'n Proto**                        |
| MessagePack / CBOR            | **msgpack-c**, nlohmann's binary modes                                                               |
| YAML                          | **yaml-cpp**, **rapidyaml** (much faster)                                                            |
| TOML                          | **toml++**                                                                                           |
| XML                           | **pugixml** (fast, sane), **tinyxml2**                                                               |
| C++ struct ↔ anything         | **glaze**, **Boost.PFR** (reflection-lite today; C++26 reflection later)                             |

## 3. Networking, HTTP, IPC

- **Asio** (standalone or Boost) — the reference async I/O model; coroutine
  support via `awaitable<T>`. The design C++26's `std::execution` descends from.
- **Boost.Beast** — HTTP/WebSocket on Asio, low-level and correct.
- **cpp-httplib** — single-header HTTP client/server, trivially embeddable.
- **libcurl** (+ `curlpp`) — the HTTP client that handles every real-world edge.
- **gRPC** — RPC with Protobuf; heavyweight but standard in services.
- **ZeroMQ** / **nng** — message-passing patterns without a broker.
- **uSockets/uWebSockets** — when throughput is the requirement.
- TLS: **OpenSSL** (everywhere), **mbedTLS** (embedded), **BoringSSL** (if you're
  already in Google's world).

## 4. Application plumbing

| Need                | Library                                                                                  |
| ------------------- | ---------------------------------------------------------------------------------------- |
| Logging             | **spdlog** (fmt-based, fast, easy), **quill** (lowest-latency, async), **glog** (legacy) |
| CLI parsing         | **CLI11** (modern, header-only), **argparse**, **cxxopts**, `Boost.ProgramOptions`       |
| Config              | **toml++**, nlohmann/json, **inih**                                                      |
| Testing             | GoogleTest, Catch2, doctest (see testing page)                                           |
| Benchmarking        | Google Benchmark, **nanobench**                                                          |
| DI / reflection     | **Boost.DI**, **RTTR**, **magic_enum** (enum↔string without macros)                      |
| Date/time pre-C++20 | Howard Hinnant's **date**                                                                |
| UUIDs               | **stduuid**                                                                              |
| Compression         | **zstd** (the default now), **lz4** (speed), **zlib** (compat)                           |
| Hashing             | **xxHash** (non-crypto, fast), **BLAKE3**, libsodium (crypto)                            |

## 5. Domain libraries

**Math / linear algebra**: **Eigen** (header-only, expression templates, the
default for dense linear algebra), **Blaze**, **Armadillo**, **xtensor**
(numpy-like), BLAS/LAPACK bindings, **GLM** (graphics-oriented vector math).

**Graphics / games**: **SDL3** (windowing/input/audio), **GLFW** (windowing only),
**bgfx** (cross-platform render abstraction), **Dear ImGui** (debug UI — install
it in every graphical project on day one), **Vulkan-Hpp**, **Metal-cpp**,
**EnTT** (ECS), **Box2D**/**Jolt**/**Bullet** (physics), **Assimp** (model
import), **stb_image** (single-header image loading).

**GUI**: **Qt** (the complete answer; licensing matters), **Dear ImGui**
(tools/debug), **wxWidgets** (native look, LGPL-ish), **Slint**, **Ultralight**/
**CEF** (embed a browser).

**Audio**: **PortAudio**, **RtAudio**, **miniaudio** (single-header),
**JUCE** (plugins/DAW), **libsndfile**.

**ML / numeric**: **libtorch** (PyTorch C++ API), **ONNX Runtime**,
**llama.cpp**/**ggml**, **OpenCV** (vision), **oneTBB** (parallelism),
**Thrust**/**CUB** (CUDA), **Kokkos** (portable HPC parallelism).

**Databases**: **SQLite** (+ **SQLiteCpp** or **sqlite_orm**), **libpq**/
**libpqxx** (Postgres), **redis-plus-plus**, **LMDB**/**RocksDB** (embedded KV).

## 6. Choosing well

- **Prefer the standard library** when it's adequate. Every dependency is a
  build-system problem, a license question, a CVE feed, and a portability risk.
- **Header-only** libraries are easy to adopt and expensive to compile. Watch
  build times when you add the fifth one.
- Check: license (GPL vs MIT/Apache/BSL matters for shipping), maintenance
  (commits in the last year), C++ standard required, whether it vendors _its_
  dependencies, and whether it works with your package manager.
- Wrap third-party APIs behind a thin interface of your own at the boundary you
  might want to swap. Do this for the ones you'd realistically replace
  (JSON, logging, HTTP), not for everything.
- Pin versions. `FetchContent` on a branch name is a time bomb.

## Gotchas

- Boost is not one library; `find_package(Boost COMPONENTS ...)` and link only
  what you use. Header-only Boost components still cost compile time.
- Abseil's "live at head" means ABI can change between releases — pin a release
  tag and don't mix Abseil versions in one binary (protobuf bundles a specific
  one, which causes real conflicts).
- nlohmann/json is ergonomic and _slow_ for large payloads and heavy on compile
  time; simdjson or glaze for hot paths.
- OpenCV pulls in an enormous dependency tree; the `core`+`imgproc` modules alone
  are usually enough.
- Qt's licensing (LGPL dynamic linking vs commercial) must be settled before you
  build a product on it.
- Mixing two libraries that each vendor a different version of the same
  dependency (protobuf, zlib, fmt) causes ODR violations and mysterious crashes.
- Header-only + `-flto` + heavy templates is the standard recipe for a 20-minute
  build. Measure with `-ftime-trace` before adding another.
