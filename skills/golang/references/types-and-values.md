# Types and values

Sources:

- https://go.dev/ref/spec
- https://go.dev/blog/slices-intro
- https://go.dev/blog/strings
- https://pkg.go.dev/builtin

## Representation decisions

Go values start at a useful zero value: numeric zero, false, empty string, nil for
pointers/functions/interfaces/slices/maps/channels. A nil slice has length and capacity
zero and works with `append` and `range`; an uninitialized map can be read but assignment
panics. Arrays own fixed storage and participate in a type by length; slices are small
descriptors over a backing array.

Appending may reuse the backing array or allocate a new one. Pass a slice when mutation
of elements is intended; return the new slice when its length can change. Use `copy` when
the caller must not share storage. A small subslice can retain a huge backing array—copy
the needed bytes/elements at a long-lived boundary.

Strings are immutable byte sequences, conventionally UTF-8 but not guaranteed valid.
Indexing yields a byte; ranging decodes UTF-8 and yields byte offsets plus runes, replacing
invalid encodings with `utf8.RuneError`. Convert deliberately among string, `[]byte`, and
`[]rune` based on bytes, encoding, or code points—not “characters” as an undefined unit.

## Control and iteration

`for` is the only loop. `range` semantics depend on the operand and language version;
do not retain addresses or closures over iteration variables without checking the module's
Go version and the desired value. Map iteration order is unspecified. A `switch` does not
fall through unless explicitly requested.

Untyped constants have arbitrary precision until given a type. Conversions are explicit;
numeric conversion may truncate or wrap according to the destination type. Named types
remain distinct even with identical underlying types.

## Gotchas

- `len(s) == 0` does not distinguish nil from non-nil empty slices; JSON often does.
- Map reads return the zero value; use the comma-ok form when absence matters.
- Copying a slice copies its descriptor, not its elements.
- Map order is never a stable serialization or test order.
- A rune is a Unicode code point, not a grapheme cluster.

