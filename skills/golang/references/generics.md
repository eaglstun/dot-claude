# Generics

Sources:

- https://go.dev/ref/spec#Type_parameter_declarations
- https://go.dev/doc/tutorial/generics
- https://go.dev/blog/when-generics
- https://go.dev/blog/comparable

## Type parameters and constraints

Type parameters make algorithms/data structures work over a family of types while
preserving static operations. Constraints are interfaces used as type sets. `~T` includes
named types whose underlying type is `T`; unions combine permitted terms. `comparable`
allows `==`/`!=` and map keys, not ordering.

```go
func Keys[M ~map[K]V, K comparable, V any](m M) []K {
    keys := make([]K, 0, len(m))
    for k := range m { keys = append(keys, k) }
    return keys
}
```

Inference uses function arguments and constraint relationships, but explicit type arguments
are sometimes clearer. The operations allowed on a type parameter are the intersection
guaranteed by its constraint, not everything supported by one member of the type set.

## When to use them

Good uses include containers, transformations whose bodies are identical across types,
and algorithms whose required operations form a clear constraint. Prefer an ordinary
interface when runtime behavior/polymorphism is the point; prefer duplicate tiny functions
when the generic abstraction is harder to read than the repetition.

Avoid constraints that exist only to expose fields—Go does not provide structural field
access over arbitrary struct types. Avoid premature “numeric” frameworks when concrete
types have materially different overflow, precision, or domain rules.

## Gotchas

- A constraint interface is not necessarily useful as an ordinary runtime value type.
- `comparable` includes interface types whose dynamic values can still panic during comparison.
- Methods cannot introduce their own type parameters beyond the receiver type's parameters.
- Type switches on a type parameter usually require conversion to `any` and lose static precision.
- Check the module's minimum Go version before adding generics (introduced in Go 1.18).

