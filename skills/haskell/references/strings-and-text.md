---
semantic_id: "4ZjGjKBZy7Saw4iSq4EVQWtrFVwzwAAB"
related_ids:
  - "6fTGTKLpyeCY-s2SIpADEWRrt14jQAAH"
  - "4Z5uMOBZxySy24SA5qEH0W9v9dx1UAAF"
---
# Strings, Text, and ByteString

Source:

- https://hackage.haskell.org/package/text
- https://hackage.haskell.org/package/bytestring
- https://hackage.haskell.org/package/text/docs/Data-Text-Encoding.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/overloaded_strings.html
- https://hackage.haskell.org/package/text-builder-linear

## 1. Which type

| Type                    | Contents              | Use for                                     |
| ----------------------- | --------------------- | ------------------------------------------- |
| `String` = `[Char]`     | Unicode chars         | tiny scripts, error messages, `Show` output |
| `Data.Text`             | Unicode, UTF-8¹       | **human-facing text — the default**         |
| `Data.Text.Lazy`        | chunked Text          | streaming/building large text               |
| `Data.ByteString`       | raw `Word8`           | **binary data, network, files**             |
| `Data.ByteString.Lazy`  | chunked bytes         | streaming binary, incremental output        |
| `Data.ByteString.Char8` | bytes viewed as ASCII | protocol headers only — see §5              |
| `Data.ByteString.Short` | compact, no slack     | many small keys held long-term              |

¹ `text ≥ 2.0` (2022) stores UTF-8 internally; earlier versions used UTF-16.
This matters for FFI and for memory estimates, not for the API.

**Rule**: bytes on the wire are `ByteString`; text in your domain is `Text`;
`String` only where an API forces it (`FilePath` in older `base`, `show`,
`error`).

`String` is a linked list of boxed `Char`s — roughly 16–20 bytes per character.
It's fine for a 40-character error message and catastrophic for a 40 MB file.

## 2. Conversions

```haskell
import qualified Data.Text as T
import qualified Data.Text.Encoding as TE
import qualified Data.ByteString as BS

T.pack   :: String -> Text
T.unpack :: Text -> String

TE.encodeUtf8       :: Text -> ByteString            -- total
TE.decodeUtf8'      :: ByteString -> Either UnicodeException Text   -- USE THIS
TE.decodeUtf8Lenient:: ByteString -> Text            -- U+FFFD for bad bytes
TE.decodeUtf8       :: ByteString -> Text            -- THROWS on invalid input ⚠

BL.toStrict / BL.fromStrict     -- lazy <-> strict ByteString (copies)
TL.toStrict / TL.fromStrict
```

`decodeUtf8` throwing an imprecise exception from pure code is the single most
common `text` bug — the failure surfaces somewhere unrelated when the value is
forced. Use `decodeUtf8'` and handle the `Left`, or `decodeUtf8Lenient` when
mangled input is acceptable.

`toStrict`/`fromStrict` copy. In a loop over chunks, that's your bottleneck.

## 3. `OverloadedStrings`

```haskell
{-# LANGUAGE OverloadedStrings #-}
name :: Text
name = "hello"                 -- fromString "hello"
```

Literals become `IsString a => a`. Two consequences:

- Ambiguity where there wasn't any: `print ("x" == "y")` needs an annotation.
- **`ByteString`'s `IsString` truncates each `Char` to 8 bits.**
  `"café" :: ByteString` gives you a mangled byte, silently. Always
  `TE.encodeUtf8 "café"` for non-ASCII bytes.

## 4. The `Text` API you actually use

```haskell
T.length, T.null, T.empty
T.append / (<>), T.concat, T.intercalate, T.unwords, T.unlines
T.splitOn, T.words, T.lines, T.chunksOf
T.strip, T.stripStart, T.stripEnd, T.stripPrefix, T.stripSuffix
T.isPrefixOf, T.isSuffixOf, T.isInfixOf
T.toUpper, T.toLower, T.toTitle, T.toCaseFold   -- toCaseFold for comparison
T.replace, T.take, T.drop, T.takeWhile, T.breakOn, T.span
T.justifyLeft, T.center
T.replicate, T.singleton
```

`T.index`/`T.length` are **O(n)** because UTF-8 is variable-width. Anything that
indexes in a loop wants a different structure (`Vector Char`, or a parser).

Case-insensitive comparison is `T.toCaseFold a == T.toCaseFold b`, not
`toLower` (which is wrong for ß, İ, and others).

## 5. `ByteString.Char8` — when it's a lie

`Data.ByteString.Char8` reinterprets `Word8` as `Char`, so it's only correct for
ASCII. `BS8.pack "café"` truncates. It's legitimate for HTTP headers, protocol
verbs, and hex — anywhere the spec guarantees ASCII — and wrong for anything
user-supplied. When in doubt, decode to `Text` at the boundary.

## 6. Building strings efficiently

Repeated `<>` on `Text`/`ByteString` is O(n²): each append copies. Use a
builder, which appends in O(1) and materializes once:

```haskell
import qualified Data.Text.Lazy.Builder as TB
import qualified Data.ByteString.Builder as BB

render :: [Item] -> TL.Text
render = TB.toLazyText . foldMap item
  where item i = TB.fromText (itemName i) <> TB.singleton '\n'

BB.toLazyByteString (BB.intDec 42 <> BB.byteString ", " <> BB.doubleDec 1.5)
```

`Data.ByteString.Builder` has fast primitives for numbers (`intDec`, `word64Hex`,
`doubleDec`) that beat `show`+`pack` by a wide margin — this is the fastest path
for writing CSV/JSON/log lines. `text-builder-linear` is faster still for `Text`.

`hPutBuilder` writes a builder straight to a handle without an intermediate
`ByteString`.

## 7. Formatting

- `printf` (`Text.Printf`) — variadic, no compile-time checking of the format
  string against arguments. Convenient, unsafe.
- `Data.Text.Format` / `formatting` — type-safe combinator formatting.
- `fmt` — `""%|x|%""` interpolation, `Buildable` class.
- `string-interpolate` / `neat-interpolation` — quasiquoted interpolation,
  which reads best for multi-line SQL/HTML.
- `show` — for **debugging output only**. `Show` is meant to produce Haskell
  syntax, not user-facing text; `displayException`/a custom `render` for the
  latter.

Numbers: `Numeric.showFFloat`/`showHex`, `Data.Text.Read.decimal`/`double`
(parsing, returns `Either String (a, Text)`), `readMaybe` for `String`.

## 8. `FilePath`, `OsPath`, and encoding at the edge

`type FilePath = String` in `base`, which cannot represent all valid OS paths
(and round-trips badly under a non-UTF-8 locale). `filepath ≥ 1.4.100` /
`OsPath` (with `System.OsPath`, and `directory`/`file-io` support) is the
correct modern type — a packed, platform-appropriate byte/word array.

Migrate at the boundary if you handle user-supplied paths; for internal
constants `FilePath` is still fine and universally supported.

## Gotchas

- **`decodeUtf8` throws from pure code.** Use `decodeUtf8'` or
  `decodeUtf8Lenient`.
- **`OverloadedStrings` + `ByteString` mangles non-ASCII literals** by
  truncating to 8 bits, with no warning.
- **`Data.ByteString.Char8` is ASCII-only** despite the friendly name.
- **`T.length` is O(n)**, and so is indexing. UTF-8 is variable width.
- **Repeated `<>` is quadratic.** Use a `Builder` for anything in a loop.
- **`toStrict`/`fromStrict` copy the whole thing.**
- **`toLower` is not case folding.** Use `toCaseFold` for comparison.
- **`String` in a hot path is ~20 bytes per character** plus pointer chasing.
- **`show` on `Text` includes the quotes and escapes** — `putStrLn (T.unpack t)`
  or `T.putStrLn t`, never `print t`, for user output.
- **Lazy `Text`/`ByteString` IO is still lazy IO**, with all the handle-lifetime
  problems from `io-and-mutable-state.md` §4.
- **`length`/`null` from `Foldable` don't work on `Text`/`ByteString`** — they
  aren't `Foldable` (they're monomorphic). That's a feature; use the qualified
  ones.
