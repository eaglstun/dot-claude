# Methods, interfaces, and embedding

Sources:

- https://go.dev/ref/spec#Method_sets
- https://go.dev/doc/faq#nil_error
- https://go.dev/blog/laws-of-reflection
- https://go.dev/wiki/CodeReviewComments#interfaces

## Method sets and receivers

Methods on `T` are available to `T` and `*T`; methods declared on `*T` belong only to
`*T`'s method set, though addressable concrete values receive convenient implicit `&`.
Interface satisfaction uses method sets without that call-site convenience. Prefer pointer
receivers when methods mutate, the value is large, or copying is unsafe; keep receiver
choice consistent for a type.

Interfaces are satisfied implicitly. Define small interfaces at the consumer when they
express exactly what that consumer needs. Return concrete types unless abstraction is part
of the API. Accepting `any` trades compile-time structure for assertions/reflection.

## The typed-nil trap

An interface value contains a dynamic type and value. It equals nil only when both are nil:

```go
var p *PathError
var err error = p
fmt.Println(err == nil) // false
```

Do not return a typed nil as an interface. Test constructors/adapters that translate
concrete pointers into interfaces.

## Embedding and type inspection

Embedding promotes methods/fields but is composition, not subclassing. It can unintentionally
expand an exported API or make a type satisfy an interface after an embedded dependency
changes. Embed behavior intentionally; name fields when delegation or API stability matters.

Use comma-ok assertions and type switches for expected alternatives. Reflection operates
on dynamic type/value pairs; values must be addressable/settable for mutation.

## Gotchas

- `*T` may satisfy an interface while `T` does not.
- A non-nil interface can hold a nil pointer and panic when its method dereferences it.
- Embedding a mutex makes copying the outer value unsafe.
- Exported broad interfaces are difficult to evolve because adding a method breaks implementers.
- Compile-time assertions (`var _ io.Reader = (*T)(nil)`) document intended satisfaction.

