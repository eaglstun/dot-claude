---
semantic_id: "p4IZT-p7nzr3Ps4E6FDbYv0b5RJQIAAN"
related_ids:
  - "54YZRjprxjj2Os7WrXXbJvU7lRBIMAAB"
  - "LQYZQepqn26yXlUAKHNbYtUrjX_YYAAB"
---
# Initialization, object lifetime, and storage duration

Source:

- https://en.cppreference.com/w/cpp/language/initialization
- https://en.cppreference.com/w/cpp/language/list_initialization
- https://en.cppreference.com/w/cpp/language/aggregate_initialization
- https://en.cppreference.com/w/cpp/language/lifetime
- https://en.cppreference.com/w/cpp/language/storage_duration
- https://en.cppreference.com/w/cpp/language/default_initialization

## 1. The initialization zoo

```cpp
int a;            // default-init: INDETERMINATE for automatic storage. Reading it is UB.
int b{};          // value-init: zero
int c = 5;        // copy-init
int d(5);         // direct-init
int e{5};         // direct-list-init
auto f = int{5};  // prvalue, elided
static int g;     // zero-initialized (static storage is always zeroed first)
```

**Braces are the default choice** (`T x{...}`) because they (a) prevent narrowing
conversions, (b) never parse as a function declaration, and (c) value-initialize
when empty. The one place to avoid them is when the type has an
`initializer_list` constructor and you meant a different one (§3).

Class members: prefer **default member initializers** so every constructor path
starts from a known state.

```cpp
struct Config {
    int    retries = 3;
    bool   verbose = false;
    std::string host;          // default-ctor'd, empty — fine
};
```

## 2. The most vexing parse

```cpp
Widget w();          // declares a FUNCTION returning Widget. Not a variable.
Widget w(Thing());   // declares a function taking a function pointer. Really.
```

Fix with braces: `Widget w{};` and `Widget w{Thing{}};`. Compilers warn
(`-Wvexing-parse` in clang) but only sometimes.

## 3. `initializer_list` hijacking

If a type has _any_ `std::initializer_list` constructor, brace-init strongly
prefers it — strongly enough to pick it over an exact match:

```cpp
std::vector<int> v1(3, 0);   // {0, 0, 0}  — size 3
std::vector<int> v2{3, 0};   // {3, 0}     — size 2!
```

So: **braces everywhere, except when calling a constructor whose arguments are
sizes/counts on a container**. `std::vector`, `std::string`, and anything with a
count+value ctor are the affected types.

## 4. Aggregates and designated initializers

An **aggregate** is a class with no user-declared/inherited constructors, no
private/protected non-static data members, no virtual functions, and no virtual
base classes. Aggregates get member-wise brace init, and (C++20) _designated
initializers_:

```cpp
struct Rect { int x = 0, y = 0, w = 0, h = 0; };

Rect r1{1, 2, 3, 4};
Rect r2{.x = 1, .h = 4};        // C++20; y and w take their default member inits
```

C++20 designators must appear **in declaration order** and cannot skip around
(unlike C, which allows out-of-order and nested array designators). Omitted
members are value-initialized (or take their default member initializer).

C++17 allows aggregate init of a class with public base classes:
`struct D : B { int i; }; D d{ {/*B*/}, 42 };`. C++20 also allows
parenthesized aggregate init `Rect r(1,2,3,4)` — which does _not_ protect
against narrowing.

## 5. Storage duration and lifetime

| Duration  | Created                                  | Destroyed                             | Notes                   |
| --------- | ---------------------------------------- | ------------------------------------- | ----------------------- |
| automatic | at declaration                           | end of enclosing block, reverse order | the stack               |
| static    | before `main` (or first use, for locals) | after `main`, reverse order           | zero-init first         |
| thread    | thread start                             | thread exit                           | `thread_local`          |
| dynamic   | `new` / allocator                        | `delete` / allocator                  | your problem — use RAII |

An object's lifetime begins when storage is obtained **and** initialization
completes; it ends when the destructor call starts (or storage is released for
trivially-destructible types). Touching an object outside that window — including
calling a virtual function from a base constructor and expecting the derived
override — is UB.

## 6. The static initialization order fiasco

Non-local statics **in different translation units** have unspecified relative
initialization order. If TU A's global constructor uses TU B's global, you may
read a zero-initialized husk.

```cpp
// BAD
extern Registry g_registry;      // in another TU
static Registrar r{g_registry};  // may run before g_registry is constructed
```

The fix is the **Meyers singleton** — a function-local static, initialized
thread-safely on first use (guaranteed since C++11):

```cpp
Registry& registry() {
    static Registry instance;    // initialized once, thread-safe, on first call
    return instance;
}
```

Destruction order is still reverse-of-construction and _can_ bite at shutdown
("static destruction order fiasco"); for that, leak deliberately
(`static Registry* p = new Registry;`) or use `std::optional` + explicit teardown.

`constinit` (C++20) asserts a variable is initialized at compile time, which
sidesteps the fiasco entirely — it is the right tool when the initializer _can_
be constant-evaluated.

## 7. Temporaries and lifetime extension

A temporary bound directly to a `const T&` or `T&&` has its lifetime extended to
that of the reference. **Only directly** — the extension does not survive a
function return, an intermediate function call, or a member reference.

```cpp
const std::string& ok   = std::string("hi");    // extended to end of scope
const std::string& also = make_struct().name;   // extended: a member of the temporary counts
const std::string& no   = id(std::string("hi"));// NOT extended: it passed through a function
const char* worse = std::string("hi").c_str();  // dangles: temp dies at the end of the full-expression
std::string_view sv = std::string("hi");        // dangles: string_view is not a reference
```

C++23's `std::ranges` and range-for got a fix here (P2718), but the classic trap
remains:

```cpp
for (char c : get_vector_of_strings()[0]) { }   // pre-C++23: the vector temp dies before the loop body
```

## Gotchas

- **`int x;` at block scope is garbage, and reading it is UB** — not "some
  arbitrary value". The optimizer is allowed to assume it never happens. At
  namespace/static scope it is zero.
- `T x{};` value-initializes but `T x;` does not — for a class with a
  user-provided default constructor they are the same, for an aggregate of
  scalars they are wildly different.
- `std::vector<int> v{3, 0}` is a two-element vector. Every C++ programmer has
  shipped this bug once.
- Narrowing inside braces is an _error_: `int x{3.5};` won't compile — this is a
  feature, and a reason to prefer braces.
- Members are initialized in **declaration order**, not in the order of the
  member-init list. Compilers warn with `-Wreorder`; heed it, because
  `A(int n) : b(n), a(b) {}` reads uninitialized `b` if `a` is declared first.
- Calling a virtual function in a constructor or destructor dispatches to the
  _current_ class's version, not the derived override. The derived object does
  not exist yet / no longer exists.
- `string_view` and `span` never extend lifetime. Binding one to a temporary is a
  dangling read; `-Wdangling-gsl` catches the easy cases only.
- A `static` local's initializer running once is guaranteed _thread-safe_, but
  recursion into it during initialization is UB (deadlock in practice).
