---
semantic_id: "KYoBAO7rixqWMsoCrGGfYbAvrZxIMAAP"
related_ids:
  - "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
  - "oYIZQevJizy_KooSq2GfY_wvmRnQIAAK"
---
# Idioms and API design

Source:

- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
- https://en.cppreference.com/w/cpp/language/attributes
- https://en.cppreference.com/w/cpp/language/enum
- https://abseil.io/tips/ (the "Totally Not Tips of the Week")
- https://google.github.io/styleguide/cppguide.html

## 1. The Core Guidelines in a dozen lines

- **P.1** Express intent directly in code. **P.4** Ideally, statically type-safe.
- **I.11** Never transfer ownership by a raw pointer or reference.
- **F.15–F.20** Prefer simple parameter passing; return by value; a "return"
  value is an output, not an out-parameter.
- **C.20** If you can avoid defining default operations, do (rule of zero).
- **C.35** A base class destructor should be public+virtual, or protected+non-virtual.
- **R.1** Manage resources automatically (RAII). **R.3** A raw pointer is non-owning.
- **ES.20** Always initialize an object. **ES.5** Keep scopes small.
- **ES.23** Prefer `{}` initializer syntax. **ES.49** Name your casts.
- **Con.1** By default, make objects immutable (`const` by default).
- **T.10** Specify concepts for all template arguments.
- **CP.20** Use RAII, never plain `lock()`/`unlock()`.

## 2. Naming and const-correctness

Whatever the convention, be consistent with the codebase. The parts that aren't
taste:

- `const` on every parameter and method that doesn't mutate. It documents,
  enables optimizations, and is nearly free to add early and painful to retrofit.
- `const` member functions must be **thread-safe** by convention (the standard
  library assumes it). A `const` getter with a lazy cache needs a mutex or an
  atomic.
- Avoid `const` on by-value parameters in _declarations_ (it's meaningless to
  the caller); it's fine in the definition.
- Don't return `const T` by value — it blocks moves.

## 3. Strong types over primitive obsession

```cpp
enum class UserId : std::int64_t {};                 // can't be confused with an OrderId
struct Meters { double value; };
struct Seconds { double value; };
Meters operator*(Seconds t, Velocity v);
```

`enum class` (scoped enums) instead of plain `enum`: no implicit int conversion,
no name leakage, explicit underlying type, forward-declarable.

```cpp
enum class Color : std::uint8_t { Red, Green, Blue };
auto c = Color::Red;
auto raw = std::to_underlying(c);                     // C++23; static_cast before that
```

For flags, either write the bitwise operators for the enum class, or use a
`std::bitset`/`struct` of bools — an unscoped enum's implicit conversions are a
recurring source of "why did this compare equal".

## 4. Attributes that carry weight

```cpp
[[nodiscard]] Result compute();                       // ignoring the return is now a warning
[[nodiscard("check for failure")]] bool try_lock();   // C++20 with a reason
class [[nodiscard]] Error { };                        // every function returning it is checked
[[maybe_unused]] auto guard = lock(m);
[[fallthrough]];
[[deprecated("use compute_v2")]] void compute_old();
struct S { [[no_unique_address]] Empty tag; int n; }; // empty member costs 0 bytes
```

`[[nodiscard]]` on every factory function, every `expected`/`optional` return,
and every RAII type is one of the highest-value/lowest-effort things you can do
to a codebase.

## 5. Casts

Name them, and prefer none:

| Cast               | Use                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------ |
| `static_cast`      | related types, numeric conversions, up/downcast without checking                                             |
| `dynamic_cast`     | polymorphic downcast **with** a runtime check (needs RTTI; returns null for pointers, throws for references) |
| `const_cast`       | removing `const` from something that was never `const` — a smell                                             |
| `reinterpret_cast` | bit-pattern reinterpretation; almost always UB for reading. Use `bit_cast`/`memcpy` instead                  |
| C-style `(T)x`     | never — it silently picks the most permissive of the above                                                   |
| `std::bit_cast`    | safe reinterpretation of trivially-copyable same-size types                                                  |

`dynamic_cast` in a hot loop is slow (string-comparison-based on some ABIs);
if you're doing it often, the design wants a `variant` or a virtual method.

## 6. Function and class API shape

```cpp
// Prefer a named struct to a bag of bools / a long parameter list
struct RenderOptions { bool wireframe = false; bool shadows = true; int msaa = 4; };
void render(const Scene&, RenderOptions opts = {});
render(scene, {.wireframe = true});                  // C++20 designated init at the call site
```

- More than ~4 parameters, or two adjacent parameters of the same type, is an
  invitation to pass them in the wrong order. Use a struct or strong types.
- `bool` parameters are unreadable at the call site (`f(true, false)`). Use an
  enum or a named options struct.
- Prefer free functions over members when they don't need private access — it
  keeps the class small and makes the function work for more types.
- Overload sets should be interchangeable in meaning; if two overloads do
  different things, name them differently.
- `explicit` on single-argument constructors and conversion operators unless
  the implicit conversion is the point.
- Make interfaces hard to misuse: no valid-but-wrong call should be spellable.
  A resource type that can't be double-freed beats documentation that says
  don't.

## 7. Standard idioms by name

**RAII** — every resource in a destructor. (See classes page.)

**PIMPL** — hide implementation, stabilize ABI, cut compile times:

```cpp
// widget.hpp
class Widget {
public:
    Widget(); ~Widget();                              // declared here, DEFINED in the .cpp
    Widget(Widget&&) noexcept; Widget& operator=(Widget&&) noexcept;
    void draw() const;
private:
    struct Impl;
    std::unique_ptr<Impl> p_;
};
```

**Copy-and-swap** — one assignment operator, strong exception guarantee:
`Widget& operator=(Widget other) { swap(*this, other); return *this; }`

**Non-virtual interface (NVI)** — public non-virtual method wraps a private
virtual one, so the base owns pre/postconditions and the derived owns only the
step.

**Type erasure** — value semantics over an open set. (See classes page.)

**CRTP / deducing `this`** — compile-time polymorphism and mixins.

**Tag dispatch** — mostly obsolete; `if constexpr` and concepts replaced it.

**Named constructors** — `static Widget fromFile(path)` beats a pile of
ambiguous constructor overloads, and can return `expected`.

**Immediately-invoked lambda** — initialize a `const` that needs logic.

**`std::exchange` in move operations** — take the value, leave a valid default.

## 8. What to avoid

- `using namespace std;` in headers (and be wary in `.cpp`).
- Macros for anything a `constexpr`, an `inline` function, or a template can do.
  Macros ignore scope and namespaces and wreck error messages. Exceptions: include
  guards, conditional compilation, and logging that needs `__FILE__`-ish context
  (and even that has `std::source_location` now).
- Raw `new`/`delete` in application code.
- Manual loops where a named algorithm exists — `std::ranges::any_of` says what
  it means; a hand-rolled loop with a `found` flag doesn't.
- Inheriting to reuse implementation (prefer composition), and deep hierarchies
  in general.
- Out-parameters when a return value or a struct would do.
- Singletons — they're globals with extra steps and they wreck testability. A
  function-local static is fine for genuinely-one-per-process resources.
- Premature `noexcept`, premature templates, and premature abstraction.
- Getters and setters for every field of a struct with no invariants; that's a
  `struct` with public members.

## Gotchas

- `const` methods promise thread-safety by convention — a mutable cache in one
  breaks callers who reasonably assumed it.
- `[[nodiscard]]` added late produces a wall of warnings; add it, then fix, in
  one commit per subsystem.
- `dynamic_cast` needs RTTI; codebases built with `-fno-rtti` (many game engines)
  can't use it, and `typeid` too.
- A `bool` parameter added "temporarily" to an existing function outlives
  everyone who understood it.
- Defaulted parameters are bound at the **call site**, so changing one in a
  shared library doesn't change existing callers — an ABI trap.
- Overloading on `T` and `T&&` plus a template constructor makes overload
  resolution unpredictable; constrain templates that could shadow a copy ctor.
- `enum class` still allows `static_cast` to any value — a cast from an out-of-
  range int is UB for the enum's underlying value range.
- Style consistency beats style correctness. Match the file you're in.
