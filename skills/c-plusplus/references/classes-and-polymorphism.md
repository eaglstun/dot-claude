---
semantic_id: "JYITQf9rzy2z6tyVq2Fbc_w_hR4AIAAF"
related_ids:
  - "oYIZQevJizy_KooSq2GfY_wvmRnQIAAK"
  - "IYIbQC-jij63usyGrWlLKvU7pdhIYAAI"
---
# Classes, special members, and polymorphism

Source:

- https://en.cppreference.com/w/cpp/language/classes
- https://en.cppreference.com/w/cpp/language/rule_of_three
- https://en.cppreference.com/w/cpp/language/virtual
- https://en.cppreference.com/w/cpp/language/derived_class
- https://en.cppreference.com/w/cpp/language/default_comparisons (C++20 `<=>`)
- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-class

## 1. The six special members and when they appear

| Member       | Implicitly declared unless…                                          |
| ------------ | -------------------------------------------------------------------- |
| default ctor | any other constructor is user-declared                               |
| destructor   | — (always, unless user-declared)                                     |
| copy ctor    | a move ctor/assign is user-declared (then **deleted**)               |
| copy assign  | a move ctor/assign is user-declared (then **deleted**)               |
| move ctor    | any of dtor / copy ctor / copy assign / move assign is user-declared |
| move assign  | any of dtor / copy ctor / copy assign / move ctor is user-declared   |

The two rows that cause real bugs: **declaring a destructor suppresses moves**
(silent pessimization) and **declaring a move deletes the copies** (loud error,
at least). "User-declared" includes `= default` written in the class body — if
you write any one of the five, write all five.

```cpp
class Buffer {
public:
    Buffer() = default;
    ~Buffer();
    Buffer(const Buffer&)            = default;
    Buffer& operator=(const Buffer&) = default;
    Buffer(Buffer&&) noexcept        = default;
    Buffer& operator=(Buffer&&) noexcept = default;
};
```

Better yet: **rule of zero.** Push resource ownership into a member
(`std::unique_ptr` with a custom deleter, `std::vector`) and declare none of them.

## 2. RAII

Every resource — memory, file descriptor, lock, GPU buffer, transaction — is
owned by an object whose destructor releases it. This is the whole ballgame; it
is why C++ needs no `defer`, no `finally`, and no GC for determinism.

```cpp
class FileHandle {
    std::FILE* f_ = nullptr;
public:
    explicit FileHandle(const char* path) : f_(std::fopen(path, "rb")) {
        if (!f_) throw std::runtime_error("open failed");
    }
    ~FileHandle() { if (f_) std::fclose(f_); }
    FileHandle(FileHandle&& o) noexcept : f_(std::exchange(o.f_, nullptr)) {}
    FileHandle& operator=(FileHandle&& o) noexcept {
        if (this != &o) { if (f_) std::fclose(f_); f_ = std::exchange(o.f_, nullptr); }
        return *this;
    }
    FileHandle(const FileHandle&)            = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    std::FILE* get() const noexcept { return f_; }
};
```

`std::exchange` is the idiomatic "take and null out" for move operations.

For one-off cleanup without writing a class, `std::unique_ptr<T, Deleter>` or a
scope-guard lambda works. (`std::experimental::scope_exit` never landed;
`absl::Cleanup` / `gsl::finally` fill the gap.)

## 3. Virtual functions

```cpp
struct Shape {
    virtual ~Shape() = default;             // REQUIRED if deleted through Shape*
    virtual double area() const = 0;        // pure virtual → abstract
    virtual void draw() const { /*...*/ }
};
struct Circle final : Shape {
    double area() const override;           // always write override
    void draw() const override;
};
```

- `virtual ~Base() = default;` on any class deleted polymorphically. Without it,
  `delete base_ptr` is UB. If the class is _not_ meant for polymorphic deletion,
  make the destructor `protected` and non-virtual.
- `override` is not optional style — it turns a silent "you created a new
  overload with a different signature" bug into a compile error.
- `final` on a class or method lets the compiler devirtualize.
- Cost: one pointer per object (the vptr), one indirect call per invocation, and
  no inlining across it. Typically 1–3 ns; fine, until it is in a per-element loop.

**Virtual dispatch does not happen in constructors or destructors.** During
`Base::Base`, the object _is_ a `Base`; calling a pure virtual there is UB
("pure virtual method called" at runtime).

## 4. Inheritance vs composition vs type erasure

| Need                                              | Tool                                    |
| ------------------------------------------------- | --------------------------------------- |
| Closed set of alternatives, known at compile time | `std::variant` + `std::visit`           |
| Open set, runtime plugins, stable ABI             | virtual base class                      |
| Open set, value semantics, no forced base class   | type erasure (see below)                |
| Reuse implementation only                         | composition (a member), not inheritance |
| Static polymorphism, zero overhead                | templates / concepts, or CRTP           |

**CRTP** (curiously recurring template pattern) gives compile-time polymorphism:

```cpp
template <class Derived>
struct Comparable {
    bool operator!=(const Comparable& o) const {
        return !static_cast<const Derived&>(*this).equals(static_cast<const Derived&>(o));
    }
};
struct Point : Comparable<Point> { bool equals(const Point&) const; };
```

Since C++23, **deducing `this`** replaces most CRTP:

```cpp
struct Comparable {
    bool operator!=(this auto const& self, auto const& o) { return !self.equals(o); }
};
```

**Type erasure** — the `std::function` / `std::any` trick — lets unrelated types
satisfy an interface without inheriting:

```cpp
class Drawable {
    struct Concept { virtual ~Concept() = default; virtual void draw() const = 0; };
    template <class T> struct Model : Concept {
        T obj;
        explicit Model(T o) : obj(std::move(o)) {}
        void draw() const override { obj.draw(); }
    };
    std::unique_ptr<Concept> self_;
public:
    template <class T> Drawable(T x) : self_(std::make_unique<Model<T>>(std::move(x))) {}
    void draw() const { self_->draw(); }
};
```

## 5. Slicing

Assigning a derived object to a base _value_ silently copies only the base
subobject:

```cpp
void render(Shape s);          // BAD: slices every argument
render(circle);                // area() now calls Shape's, not Circle's
```

Pass polymorphic types by `const Base&`, `Base*`, or a smart pointer. Prevent it
structurally by making the base abstract, or by deleting the base's copy
assignment.

## 6. Operators and `<=>`

C++20's three-way comparison collapses six operators into one:

```cpp
struct Version {
    int major, minor, patch;
    auto operator<=>(const Version&) const = default;   // gives < <= > >=
    bool operator==(const Version&) const = default;    // gives == and !=
};
```

`= default` compares members lexicographically in declaration order. Write both
`<=>` and `==` when defaulting — `==` is _not_ synthesized from a user-provided
`<=>` (only from a defaulted one), and defaulted `==` is faster for containers.

Return types: `std::strong_ordering` (substitutable), `std::weak_ordering`
(equivalent but distinguishable, e.g. case-insensitive strings),
`std::partial_ordering` (may be unordered, e.g. floats → this is what `double`
members give you).

Prefer **hidden friends** for symmetric binary operators — defined inside the
class as `friend`, found only by ADL, which keeps overload sets small and error
messages short:

```cpp
struct Money {
    long cents;
    friend Money operator+(Money a, Money b) { return {a.cents + b.cents}; }
};
```

## 7. Access, `explicit`, and other hygiene

- Single-argument constructors: mark `explicit` unless implicit conversion is
  genuinely wanted. C++20 also allows `explicit(bool)` for conditional
  explicitness in templates.
- Conversion operators: mark `explicit` too (`explicit operator bool()` is the
  one idiomatic exception, since it still works in `if`/`while` contexts).
- `struct` for aggregates of public data, `class` when there are invariants.
- Prefer `private` members + narrow public methods; a class with no invariants
  should just be a `struct`.
- The **PIMPL** idiom hides implementation and stabilizes ABI:
  `std::unique_ptr<Impl> p_;` — note the destructor must be _declared_ in the
  header and _defined_ in the .cpp, after `Impl` is complete, or you get
  "invalid application of sizeof to incomplete type".

## Gotchas

- Missing `virtual ~Base()` → `delete` through a base pointer is UB and leaks the
  derived members. `-Wdelete-non-virtual-dtor` catches it.
- A user-declared destructor kills implicit move; the class quietly copies forever.
- `override` misspelled as a comment (`// override`) protects nothing. Use the keyword.
- Calling virtuals from constructors/destructors dispatches statically.
- Passing a polymorphic type by value slices it; there is no warning by default.
- Defaulted `<=>` with a `double` member yields `partial_ordering`, so the type
  cannot be used as a `std::set` key without a custom comparator.
- Non-virtual functions are _hidden_, not overridden, by a same-named derived
  function — and a derived overload hides **all** base overloads of that name.
  `using Base::f;` in the derived class restores them.
- Multiple inheritance from two classes with a common base needs `virtual`
  inheritance or you get two base subobjects; prefer interfaces (pure-virtual,
  no state) to avoid the diamond entirely.
