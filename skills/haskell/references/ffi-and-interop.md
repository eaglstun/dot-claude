---
semantic_id: "6Y3HtaQ5-3F58oKTaoGncWB6jdQXwAAA"
related_ids:
  - "aYz2IabZa9AS79yCbqOD0WpuhdwzQAAK"
  - "4ZjGjKBZy7Saw4iSq4EVQWtrFVwzwAAB"
---
# FFI and interop

Source:

- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/ffi.html
- https://www.haskell.org/onlinereport/haskell2010/haskellch8.html (FFI chapter)
- https://hackage.haskell.org/package/base/docs/Foreign.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/wasm.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/javascript.html

## 1. Importing a C function

```haskell
{-# LANGUAGE ForeignFunctionInterface #-}   -- in GHC2021
module Crypto where

import Foreign
import Foreign.C.Types
import Foreign.C.String

foreign import ccall unsafe "string.h strlen"
  c_strlen :: CString -> IO CSize

foreign import ccall safe "crypto_hash"
  c_hash :: Ptr Word8 -> CSize -> Ptr Word8 -> IO CInt
```

**`unsafe` vs `safe` is the decision that matters:**

|                            | `unsafe`                             | `safe`                            |
| -------------------------- | ------------------------------------ | --------------------------------- |
| Overhead                   | a few ns                             | ~100ns+ (releases the capability) |
| May call back into Haskell | **no**                               | yes                               |
| May block                  | **no** — blocks the whole capability | yes                               |
| GC during the call         | cannot happen                        | can                               |

Use `unsafe` for short, non-blocking, non-callback-invoking functions (the
majority — `strlen`, `memcmp`, a math function). Use `safe` for anything that
does IO, sleeps, takes a lock, or calls a Haskell callback. Getting this wrong
with `unsafe` on a blocking call **freezes every Haskell thread on that
capability** and is nearly impossible to diagnose from the symptoms.

`interruptible` is a third variant: like `safe`, but `throwTo` can interrupt it
via a signal.

## 2. Types across the boundary

`Foreign.C.Types` gives `CInt`, `CUInt`, `CLong`, `CSize`, `CChar`, `CDouble`,
`CFloat`, `CBool`, `CTime` — use these, never `Int` for a C `int` (their sizes
differ per platform).

Marshallable types: `Ptr a`, `FunPtr a`, `CInt` etc., `Int`/`Word` (machine
word), `Double`/`Float`, `Char`, `Bool`, `()` as a return, and newtypes over
those. `String`, `Text`, and ADTs must be marshalled explicitly.

```haskell
withCString      :: String -> (CString -> IO a) -> IO a        -- locale-encoded
withCStringLen   :: String -> (CStringLen -> IO a) -> IO a
peekCString      :: CString -> IO String
BS.useAsCString  :: ByteString -> (CString -> IO a) -> IO a    -- NUL-terminated copy
BS.useAsCStringLen :: ByteString -> (CStringLen -> IO a) -> IO a  -- no copy if possible
BS.packCString   :: CString -> IO ByteString
alloca           :: Storable a => (Ptr a -> IO b) -> IO b      -- out-parameters
allocaBytes      :: Int -> (Ptr a -> IO b) -> IO b
with             :: Storable a => a -> (Ptr a -> IO b) -> IO b
withArray        :: Storable a => [a] -> (Ptr a -> IO b) -> IO b
peek / poke / peekElemOff / pokeElemOff
```

Every `with*` is `bracket`-based — the buffer is freed on exit, including on
exception, and **is invalid afterwards**. Returning a `Ptr` out of a `with`
block is the classic use-after-free in Haskell.

`Storable` instances define `sizeOf`, `alignment`, `peek`, `poke` for a struct:

```haskell
data Point = Point CDouble CDouble
instance Storable Point where
  sizeOf    _ = 16
  alignment _ = 8
  peek p      = Point <$> peekByteOff p 0 <*> peekByteOff p 8
  poke p (Point x y) = pokeByteOff p 0 x >> pokeByteOff p 8 y
```

Hand-computing offsets is how you get a corrupt struct on a different platform.
Use **`hsc2hs`** instead (§4).

## 3. Pinned memory and `ForeignPtr`

GHC's GC moves objects, so a `Ptr` into the Haskell heap is only valid while the
GC is prevented from moving it.

```haskell
mallocForeignPtrBytes :: Int -> IO (ForeignPtr a)      -- pinned, GC-managed
newForeignPtr finalizerFree ptr                        -- attach a C free()
withForeignPtr fp $ \p -> c_use p                      -- keeps it alive for the block
```

A `ForeignPtr` carries a finalizer that runs when the GC collects it — at an
_unspecified_ time, which makes it the wrong tool for scarce resources like file
descriptors (use `bracket` for those).

`ByteString` is backed by a pinned `ForeignPtr`, which is why
`useAsCStringLen` can avoid copying. `Data.Vector.Storable` likewise
(`unsafeWith`). Boxed `Vector` and `Text` are **not** directly usable as C
buffers.

**`withForeignPtr` is required around any use of the raw pointer.** Without it,
GHC may consider the `ForeignPtr` dead and run the finalizer while C is still
reading. (GHC 9.x's `unsafeWithForeignPtr` skips a `touch#` and is only safe if
you can prove liveness some other way.)

## 4. `hsc2hs` and `c2hs`

`hsc2hs` preprocesses a `.hsc` file, letting the C compiler compute sizes,
offsets, and constant values:

```haskell
#include <sys/stat.h>

data Stat = Stat { stSize :: COff, stMode :: CMode }

instance Storable Stat where
  sizeOf    _ = #{size struct stat}
  alignment _ = #{alignment struct stat}
  peek p = Stat <$> #{peek struct stat, st_size} p
                <*> #{peek struct stat, st_mode} p

oRdOnly :: CInt
oRdOnly = #{const O_RDONLY}
```

Cabal handles `.hsc` files automatically (list the module normally). This is the
right way to bind any real C API — offsets and flag values differ between
platforms and libc versions.

`c2hs` goes further (parses headers, generates the `foreign import`s), at the
cost of a heavier, occasionally fragile toolchain.

## 5. Calling Haskell from C

```haskell
foreign export ccall hs_add :: CInt -> CInt -> IO CInt
hs_add a b = pure (a + b)
```

GHC generates a header (`Module_stub.h`). The C side must initialize the
runtime:

```c
#include <HsFFI.h>
int main(int argc, char *argv[]) {
    hs_init(&argc, &argv);
    printf("%d\n", hs_add(2, 3));
    hs_exit();
    return 0;
}
```

For a shared library used by a non-Haskell main, call `hs_init` from a
constructor (`__attribute__((constructor))`) or an explicit init function, and
build with `-shared -dynamic -fPIC`. Callbacks _into_ Haskell need
`foreign import ccall "wrapper"` to turn a Haskell function into a `FunPtr`:

```haskell
foreign import ccall "wrapper" mkCallback :: (CInt -> IO ()) -> IO (FunPtr (CInt -> IO ()))
-- freeHaskellFunPtr when done, or you leak
```

A C thread that calls into Haskell must be a "bound" thread or go through the
RTS's thread adoption; this is where `-threaded` becomes mandatory.

## 6. Cabal wiring

```cabal
library
  c-sources:          cbits/helpers.c
  include-dirs:       cbits
  install-includes:   myapp.h
  extra-libraries:    z crypto          -- links -lz -lcrypto
  pkgconfig-depends:  libsodium >= 1.0
  cc-options:         -O2 -Wall
  ld-options:         -Wl,--no-as-needed
  build-tool-depends: hsc2hs:hsc2hs
```

`pkgconfig-depends` is the portable way to find a system library;
`extra-lib-dirs`/`extra-include-dirs` (often via `~/.cabal/config` or
`--extra-lib-dirs`) for Homebrew/Nix paths on macOS.

## 7. Other targets

- **JavaScript backend** (GHC 9.6+, from GHCJS): `javascript-ffi` imports,
  `foreign import javascript`. Usable for real apps (`miso`, `reflex-dom`),
  with a large output size.
- **WASM backend** (GHC 9.6+): `foreign import javascript` via the wasm
  reactor model, `wasm32-wasi-ghc` from ghcup's cross-compiler channel. Rapidly
  improving; check the current release notes before planning on it.
- **Python**: no first-class bridge; expose a C ABI from Haskell and call it
  with `ctypes`/`cffi`, or talk over a socket/subprocess. `inline-python`
  exists but is niche.
- **C++**: no direct support — write an `extern "C"` shim. `inline-c` and
  `inline-c-cpp` let you embed C/C++ snippets in Haskell source with automatic
  marshalling, which is often the fastest route for a small binding.
- **Rust**: same as C — `#[no_mangle] extern "C"` on the Rust side, ordinary
  `foreign import ccall` on the Haskell side.

## Gotchas

- **`unsafe` on a blocking call freezes the capability** — with `-N1`, the whole
  program. This is the most damaging FFI mistake.
- **`unsafe` foreign calls must not call back into Haskell**; doing so corrupts
  the RTS rather than failing cleanly.
- **A `Ptr` from `alloca`/`withCString` is dangling after the block.**
- **`withForeignPtr` is mandatory** around raw-pointer use; without it the
  finalizer can run mid-call.
- **`CInt` ≠ `Int`.** Use `Foreign.C.Types` for anything crossing the boundary.
- **`withCString` uses the locale encoding**, not UTF-8. For bytes, go through
  `ByteString`.
- **`FunPtr`s from `wrapper` imports leak** unless you `freeHaskellFunPtr`.
- **Hand-written struct offsets break on another platform.** Use `hsc2hs`.
- **`ForeignPtr` finalizers run at GC time, not scope exit** — never use them
  for file descriptors, locks, or anything scarce.
- **Haskell exceptions cannot propagate through C frames.** Catch at the FFI
  boundary and return an error code.
- **The RTS must be initialized (`hs_init`) before any exported Haskell
  function is called**, including from a library constructor.
