---
semantic_id: "lPD-DXbp6RT7h5y4CJExUbg6VkUpIAAH"
related_ids:
  - "nPDrGXZ47LT6kp2oDKWyUalrUlSpIAAF"
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
---
# Serde

Source:

- <https://serde.rs/> (the guide: attributes, custom impls, data model)
- <https://serde.rs/attributes.html> (the full container/variant/field attribute list)
- <https://serde.rs/enum-representations.html> (externally/internally/adjacently/untagged)
- <https://docs.rs/serde_json/latest/serde_json/>
- <https://docs.rs/serde_with/latest/serde_with/>

## 1. Setup

```toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

The `derive` feature is not on by default, and forgetting it produces "cannot find derive
macro `Serialize`". In a workspace, put the feature on the workspace dependency.

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Config {
    listen_port: u16,                                  // "listenPort"
    #[serde(default = "default_workers")]
    workers: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    tls_cert: Option<String>,
    #[serde(alias = "log_level")]
    level: String,
}
fn default_workers() -> usize { 4 }
```

Serde is format-agnostic: the same derives feed JSON, TOML, YAML, MessagePack, bincode,
CSV, and everything else, because the derive targets serde's own data model rather than a
format.

## 2. The attributes that carry the weight

**Container:**

| attribute                                      | effect                                                                |
| ---------------------------------------------- | --------------------------------------------------------------------- |
| `rename_all = "camelCase"`                     | also `snake_case`, `kebab-case`, `PascalCase`, `SCREAMING_SNAKE_CASE` |
| `deny_unknown_fields`                          | error instead of ignoring extra input keys                            |
| `default`                                      | missing fields fall back to `Default::default()`                      |
| `transparent`                                  | a one-field newtype serialises as the inner value                     |
| `tag`, `tag` + `content`, `untagged`           | enum representation, see below                                        |
| `from = "T"` / `into = "T"` / `try_from = "T"` | convert through a wire-format struct                                  |
| `bound = "..."`                                | override the derived `where` clause on generics                       |
| `crate = "..."`                                | when serde is re-exported under another name                          |

**Field:**

| attribute                                        | effect                                                          |
| ------------------------------------------------ | --------------------------------------------------------------- |
| `rename = "id"`, `alias = "ID"`                  | rename both ways; alias accepts extra input names               |
| `default` / `default = "path"`                   | missing field is allowed                                        |
| `skip`, `skip_serializing`, `skip_deserializing` | omit entirely                                                   |
| `skip_serializing_if = "Option::is_none"`        | omit when the predicate holds                                   |
| `with = "module"`                                | module providing `serialize`/`deserialize`                      |
| `serialize_with` / `deserialize_with`            | one function each                                               |
| `flatten`                                        | inline a nested struct's fields, or capture the rest into a map |
| `borrow`                                         | zero-copy `&'a str` / `&'a [u8]`                                |

## 3. Enum representations

```rust
enum Msg { Ping, Text { body: String } }
```

| representation     | attribute                            | JSON for `Text`                  |
| ------------------ | ------------------------------------ | -------------------------------- |
| external (default) | none                                 | `{"Text":{"body":"hi"}}`         |
| internal           | `#[serde(tag = "type")]`             | `{"type":"Text","body":"hi"}`    |
| adjacent           | `#[serde(tag = "t", content = "c")]` | `{"t":"Text","c":{"body":"hi"}}` |
| untagged           | `#[serde(untagged)]`                 | `{"body":"hi"}`                  |

Internally tagged is what most hand-written JSON APIs look like, and it is the one to reach
for when you control the schema. It cannot represent tuple variants or newtype variants
wrapping non-struct types, which is the constraint that pushes people to adjacent tagging.

Untagged tries each variant in order and returns the first that parses. It is the only
option for schemas you do not control, and it is a debugging tar pit: any failure reports
"data did not match any variant of untagged enum Msg" with no indication of which variant
was closest or why it failed. Order the variants most-specific first, and consider a manual
`Deserialize` impl that peeks at a discriminating field instead.

## 4. Escape hatches

**`with` module** for a type you do not own, in a format you do not control:

```rust
#[derive(Deserialize)]
struct Row {
    #[serde(with = "unix_ts")]
    at: SystemTime,
}

mod unix_ts {
    use serde::{Deserialize, Deserializer, Serializer};
    pub fn serialize<S: Serializer>(t: &std::time::SystemTime, s: S) -> Result<S::Ok, S::Error> {
        let secs = t.duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();
        s.serialize_u64(secs)
    }
    pub fn deserialize<'de, D: Deserializer<'de>>(d: D) -> Result<std::time::SystemTime, D::Error> {
        let secs = u64::deserialize(d)?;
        Ok(std::time::UNIX_EPOCH + std::time::Duration::from_secs(secs))
    }
}
```

**`try_from`** when validation belongs in the type: deserialize into a raw struct, then run
your constructor. This is the cleanest way to make "parsed" mean "valid".

**`serde_with`** removes most hand-written `with` modules:

```rust
#[serde_with::serde_as]
#[derive(Deserialize)]
struct S {
    #[serde_as(as = "DisplayFromStr")] port: u16,           // "8080" -> 8080
    #[serde_as(as = "Vec<DisplayFromStr>")] ids: Vec<Uuid>,
    #[serde_as(as = "OneOrMany<_>")] tags: Vec<String>,      // "a" or ["a","b"]
    #[serde_as(as = "TimestampSeconds<i64>")] at: SystemTime,
}
```

**Untyped**: `serde_json::Value` when the shape is genuinely unknown, and
`serde_json::value::RawValue` when you want to pass a sub-document through without parsing
it (a big win for proxies).

**Catch-all field**: `#[serde(flatten)] extra: HashMap<String, Value>` collects everything
not otherwise claimed.

## 5. Zero-copy deserialization

```rust
#[derive(Deserialize)]
struct Row<'a> {
    #[serde(borrow)]
    name: &'a str,
}
let row: Row = serde_json::from_str(&buf)?;   // borrows from buf, no allocation
```

Only works when the input is in memory (`from_str` / `from_slice`), never `from_reader`,
and only for strings with no escape sequences (an escaped string must be unescaped into a
new allocation, so serde falls back to an error unless the field is `Cow<'a, str>`).
`Cow<'a, str>` with `#[serde(borrow)]` is the robust version: borrow when possible, allocate
when not.

## 6. Format crates

| format      | crate                                                               | note                             |
| ----------- | ------------------------------------------------------------------- | -------------------------------- |
| JSON        | `serde_json`                                                        | self-describing, the default     |
| JSON, fast  | `simd-json`, `sonic-rs`                                             | drop-in-ish, meaningful speedups |
| TOML        | `toml`                                                              | config files                     |
| YAML        | `serde_yaml` is unmaintained; use `serde_norway` or `serde_yaml_ng` |                                  |
| MessagePack | `rmp-serde`                                                         | compact, self-describing         |
| bincode     | `bincode`                                                           | fastest, **not** self-describing |
| postcard    | `postcard`                                                          | no_std/embedded, compact         |
| CBOR        | `ciborium`                                                          |                                  |
| CSV         | `csv`                                                               | flat records only                |

"Self-describing" matters: a non-self-describing format (bincode, postcard) cannot support
`flatten`, `untagged`, or `deserialize_any`, and will fail at runtime rather than compile
time if you use them.

## Gotchas

- **`#[serde(flatten)]` silently disables `deny_unknown_fields`** on the container, because
  flatten needs to buffer unknown keys to hand to the inner type. The two attributes are
  mutually exclusive and the compiler does not say so.
- `flatten` also buffers into a map, which **breaks non-self-describing formats** (bincode
  fails at runtime) and changes number types: an integer may come back through the buffer as
  a float in some formats.
- `skip_serializing_if = "Option::is_none"` handles the write side only. Without a matching
  `#[serde(default)]`, deserializing a document that omits the field is a hard error.
- `#[serde(default)]` on the **container** applies to every field and requires the whole
  struct to implement `Default`. On a field it does not.
- Untagged enum errors are useless by construction: no variant name, no field, no position.
  Budget for this before choosing untagged.
- Two variants that can both match the same input under `untagged` resolve to whichever is
  declared first, silently. Reordering variants is a behaviour change.
- `u64`/`i64` values above 2^53 survive `serde_json` fine but lose precision the moment a
  JavaScript consumer parses them. Serialise large IDs as strings (`serde_with::DisplayFromStr`).
- `serde_json::Value` object key order is not preserved unless you enable the
  `preserve_order` feature (which switches to `IndexMap`).
- `from_reader` is usually **slower** than reading to a `String` and calling `from_str`,
  because it cannot use the SIMD-ish fast paths or borrow. Read to memory when the document
  fits.
- Deriving on a generic struct adds `T: Serialize` bounds to every parameter, including ones
  that never appear in a serialized field. Fix with `#[serde(bound = "")]`.
- `chrono`, `uuid`, `url`, `indexmap`, and friends all need their **own** `serde` feature
  enabled; the error is "the trait bound `Uuid: Serialize` is not satisfied".
- `deny_unknown_fields` on a public API type means adding a field to the _sender_ breaks
  older receivers. It is the right default for config files and the wrong one for wire
  protocols you intend to evolve.
- `#[serde(rename_all = "camelCase")]` renames fields, not variants; variants need
  `rename_all` on the enum itself, and both can be applied with
  `rename_all_fields` for variant contents.
