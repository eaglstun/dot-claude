---
semantic_id: "YZjGBCDZwwy4_Yiw5KGLU09_4l43UAAO"
related_ids:
  - "4Z5uMOBZxySy24SA5qEH0W9v9dx1UAAF"
  - "bR3iBSDJo6iY44yOrpON1W5vz383EAAE"
---
# JSON and serialization

Source:

- https://hackage.haskell.org/package/aeson
- https://hackage.haskell.org/package/aeson/docs/Data-Aeson.html
- https://hackage.haskell.org/package/binary
- https://hackage.haskell.org/package/serialise
- https://hackage.haskell.org/package/cassava

## 1. `aeson` basics

```haskell
import Data.Aeson

encode  :: ToJSON a   => a -> BL.ByteString
decode  :: FromJSON a => BL.ByteString -> Maybe a
eitherDecode :: FromJSON a => BL.ByteString -> Either String a   -- prefer this
encodeFile / decodeFileStrict'
```

The `Value` type:

```haskell
data Value = Object Object | Array Array | String Text
           | Number Scientific | Bool Bool | Null
```

**aeson 2.x** changed `Object` from `HashMap Text Value` to
`KeyMap Value` with a distinct `Key` type (`Data.Aeson.Key`,
`Data.Aeson.KeyMap`), to fix hash-collision DoS. Code written for aeson 1.x
needs `Key.fromText`/`Key.toText` and `KeyMap` in place of `HashMap` — this is
the migration you'll hit in any older codebase.

Numbers are `Scientific` (arbitrary precision), so round-tripping a `Double`
through JSON is exact-ish but converting to `Int` needs care
(`Data.Scientific.toBoundedInteger`).

## 2. Instances by hand

```haskell
instance ToJSON User where
  toJSON u = object
    [ "id"    .= userId u
    , "name"  .= userName u
    , "email" .= userEmail u          -- Maybe: emits null
    ]
  -- also define toEncoding for speed: it skips building a Value
  toEncoding u = pairs ("id" .= userId u <> "name" .= userName u)

instance FromJSON User where
  parseJSON = withObject "User" $ \o -> User
    <$> o .:  "id"
    <*> o .:  "name"
    <*> o .:? "email"                 -- optional → Maybe
    <*> o .:? "role" .!= RoleUser     -- optional with default
```

`.:` fails on a missing key, `.:?` gives `Nothing`, `.!=` supplies a default.
`withObject "User"` names the type in the error message — always pass a useful
label, it's the difference between a usable parse error and "expected Object".

**Define `toEncoding`.** `toJSON` builds an intermediate `Value` tree;
`toEncoding` writes directly to a `Builder` and is substantially faster for
serialization-heavy services. `toEncoding = genericToEncoding defaultOptions`
if you're deriving.

## 3. Generic deriving and `Options`

```haskell
{-# LANGUAGE DeriveGeneric, DeriveAnyClass #-}
data User = User { userId :: Int, userName :: Text }
  deriving stock (Generic, Show)
  deriving anyclass (ToJSON, FromJSON)
```

Field mangling via `Options`:

```haskell
customOptions :: Options
customOptions = defaultOptions
  { fieldLabelModifier     = camelTo2 '_' . dropPrefix "user"
  , omitNothingFields      = True          -- drop null fields entirely
  , constructorTagModifier = map toLower
  , sumEncoding            = TaggedObject "type" "contents"   -- default
  , allNullaryToStringTag  = True
  , rejectUnknownFields    = True          -- aeson 2.x: strict decoding
  }

instance ToJSON   User where toJSON    = genericToJSON    customOptions
                             toEncoding = genericToEncoding customOptions
instance FromJSON User where parseJSON = genericParseJSON customOptions
```

`sumEncoding` options — `TaggedObject` (default),
`ObjectWithSingleField`, `TwoElemArray`, `UntaggedValue` — change the wire
format for sum types. Pick one at the start of a project; changing it later is a
breaking API change to every client.

`deriving via` with `aeson`'s `CustomJSON` (from `deriving-aeson`) is the tidy
way to attach options without writing instance bodies:

```haskell
deriving (ToJSON, FromJSON)
  via CustomJSON '[FieldLabelModifier (StripPrefix "user", CamelToSnake)] User
```

## 4. Errors and partial decoding

`eitherDecode` gives a string. For structured paths, `iparse`/`ifromJSON`
(aeson's `JSONPath`-carrying variants) report `$.users[2].name` style locations —
worth wiring in for config files where the user needs to find the mistake.

```haskell
case eitherDecode bs of
  Left err -> hPutStrLn stderr ("bad JSON: " <> err)
  Right v  -> ...
```

`decode` returning `Maybe` throws away the reason. Never use it in code a human
will have to debug.

Streaming large JSON: `aeson`'s `json` parser over `attoparsec` for incremental
input, or `json-stream`/`conduit-aeson` for documents that don't fit in memory.
`decodeFileStrict'` (note the tick — strict) for ordinary files.

## 5. Poking at JSON without types

```haskell
import Data.Aeson.Lens        -- from lens-aeson
v ^? key "data" . key "items" . nth 0 . key "name" . _String
v ^.. key "items" . values . key "id" . _Integer
```

Perfect for exploration, one-off scripts, and APIs you don't control the shape
of. In production code, parse into a real type at the boundary — the point of
Haskell is that everything downstream then can't be wrong.

## 6. Binary formats

| Package                 | Format                | Notes                                          |
| ----------------------- | --------------------- | ---------------------------------------------- |
| `binary`                | custom, ad hoc        | in `base`'s orbit; **no version tolerance**    |
| `cereal`                | custom, strict        | like `binary` but strict, `Get`/`Put`          |
| `serialise`             | CBOR (RFC 8949)       | standard, cross-language, compact              |
| `store`                 | machine-native layout | fastest; **not portable across architectures** |
| `flat`                  | bit-packed            | very compact                                   |
| `protobuf`/`proto-lens` | Protobuf              | schema-first, cross-language                   |

```haskell
import Codec.Serialise
bs <- pure (serialise myValue)
v  <- either throwIO pure (deserialiseOrFail bs)
```

**Derived binary instances are not a schema.** Adding a constructor or
reordering fields silently changes the format, and old data decodes into garbage
rather than failing. If the bytes outlive the process — cache files, on-disk
state, messages between versions — put an explicit version tag in front and
handle it, or use a schema'd format (CBOR with explicit tags, protobuf).

## 7. CSV and YAML

```haskell
-- cassava
import Data.Csv
instance FromNamedRecord User where
  parseNamedRecord r = User <$> r .: "id" <*> r .: "name"
decodeByName :: BL.ByteString -> Either String (Header, Vector a)
```

`cassava` handles quoting/escaping properly; hand-rolled `splitOn ","` does not.
`Data.Csv.Incremental` streams.

YAML: the `yaml` package reuses your `aeson` instances
(`Data.Yaml.decodeFileEither`, `encodeFile`), which makes it the path of least
resistance for config. Its error messages carry line numbers, unlike aeson's.

TOML: `toml-reader` or `tomland`.

## 8. Dates and times on the wire

`aeson` encodes `UTCTime` as ISO-8601 with a `Z`, and `Day` as `YYYY-MM-DD`.
`ZonedTime` round-trips the offset. `NominalDiffTime` encodes as a number of
seconds. If the other end sends epoch millis (very common), write a `newtype`
with a custom instance rather than an orphan on `UTCTime`:

```haskell
newtype EpochMillis = EpochMillis UTCTime
instance FromJSON EpochMillis where
  parseJSON = withScientific "EpochMillis" $
    pure . EpochMillis . posixSecondsToUTCTime . realToFrac . (/ 1000)
```

## Gotchas

- **aeson 2.x's `Object` is `KeyMap`, not `HashMap Text`.** Old code and old
  StackOverflow answers won't compile.
- **`decode` hides the error.** Use `eitherDecode`/`decodeFileStrict'`.
- **`.:` on a `Maybe` field succeeds with `Just Nothing` semantics you didn't
  want** — `.:?` is for "key may be absent", `.:` + `Maybe` is for "key present,
  value may be null". They differ, and the difference is a real bug.
- **`omitNothingFields = False` (the default) emits `"email": null`**, which
  some strict consumers reject.
- **Generic instances mirror your Haskell field names**, so renaming a field
  silently changes your API. Pin the wire names with `Options` or explicit
  instances.
- **Not defining `toEncoding` costs real throughput** in an API server.
- **`binary`/`store` derived instances have no versioning**; a data type change
  silently corrupts old data. `store` also isn't portable across architectures.
- **`Scientific` → `Int` can silently truncate or overflow.** Use
  `toBoundedInteger`.
- **Sum encodings are wire-format decisions.** Changing `sumEncoding` later
  breaks every client.
- **JSON object key order is not preserved** by `KeyMap`; golden tests must
  compare parsed values or sort keys.
