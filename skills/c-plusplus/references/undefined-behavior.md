---
semantic_id: "vYqKaX5jipqXNo4AqHW_87kPuRRQAAAO"
related_ids:
  - "KYoBAO7rixqWMsoCrGGfYbAvrZxIMAAP"
  - "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
---
# Undefined behavior and the sanitizers that find it

Source:

- https://en.cppreference.com/w/cpp/language/ub
- https://en.cppreference.com/w/cpp/language/eval_order
- https://en.cppreference.com/w/cpp/language/reinterpret_cast (strict aliasing)
- https://clang.llvm.org/docs/AddressSanitizer.html
- https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
- https://clang.llvm.org/docs/ThreadSanitizer.html

## 1. What UB actually means

UB is not "unpredictable result". It is **a promise you made to the optimizer**.
The compiler assumes UB never happens and rewrites code accordingly, so a null
check _after_ a dereference gets deleted, an infinite loop with no side effects
gets removed, and a signed overflow check written as `a + b < a` evaporates.
The symptom typically appears far from the cause, and only at `-O2`, and only in
the build that shipped.

Three flavors:

- **Undefined**: anything may happen. (Most of this page.)
- **Unspecified**: one of several valid behaviors, no documentation required
  (e.g. order of evaluation of function arguments).
- **Implementation-defined**: valid behaviors, documented (e.g. `sizeof(int)`,
  whether `char` is signed).

## 2. The catalogue

**Memory**

- Out-of-bounds read or write, including `v[v.size()]` and one-past-the-end
  dereference. `at()` throws, `operator[]` does not check.
- Use after free / use after return of a local's address.
- Double free, mismatched `new`/`delete[]`.
- Reading an uninitialized automatic variable.
- Null dereference — including `this` being null in a member call.
- Misaligned load/store through a cast pointer.

**Arithmetic**

- **Signed** integer overflow (unsigned wraps — that is defined).
- Division or modulo by zero.
- Shift by ≥ the width of the type, or a negative shift count.
  `1 << 31` on `int` is UB; `1u << 31` is fine.
- Converting a floating value to an integer type it cannot represent.

**Objects and types**

- **Strict aliasing**: accessing an object through a pointer to an unrelated
  type. `*(float*)&int_value` is UB even though it "works".
- Using an object before its lifetime starts or after it ends.
- Calling a virtual function on a partially-constructed object through a base.
- Modifying a `const` object, or an object declared `const` via a `const_cast`.
- Casting a function pointer to an object pointer and back through the wrong type.

**Control flow**

- Falling off the end of a non-`void` function. (Compilers often emit no code at
  all for the path — a favourite source of "the function returned garbage".)
- Infinite loop with no side effects and no I/O (C++11 forward-progress rule).
- Recursion deep enough to smash the stack is not _technically_ UB but is
  equally fatal.

**Concurrency**

- A data race: two threads, same memory, at least one write, no synchronization.
- Deadlock is not UB — it is just a hang. A race is far worse.

**Library preconditions**

- Dereferencing `end()`, invalidated iterators (see containers page),
  `std::string_view` over a dead buffer, `.front()`/`.back()` on empty,
  `std::optional::operator*` when empty, `std::get` on the wrong `variant`
  alternative (that one throws, actually), passing overlapping ranges to
  `std::copy` (use `copy_backward` / `memmove`).

## 3. Evaluation order

C++17 fixed the worst of it, but did not make everything ordered:

```cpp
i = i++ + 1;             // UB before C++17; well-defined (but awful) after
f(g(), h());             // order of g() and h() is UNSPECIFIED, even in C++20
a[i] = i++;              // C++17: right side sequenced before left. OK but unreadable.
std::cout << f() << g(); // C++17: left-to-right guaranteed for << chains
```

C++17 rules worth knowing: in `a = b`, `b` is evaluated first; in `a[b]`, `a`
first; in `a.b(args)`, the postfix expression before the args; `<<` and `>>`
chains are strictly left-to-right. Function argument evaluation is still
interleaved-in-unspecified-order (though no longer _indeterminately sequenced_,
so it can't interleave the evaluations themselves).

## 4. Sanitizers — use them, they are free

```bash
# ASan + UBSan together: the everyday debug build
-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1

# Thread races (cannot combine with ASan)
-fsanitize=thread -g -O1

# Uninitialized reads (clang only; needs the whole program instrumented, libc++ included)
-fsanitize=memory -fsanitize-memory-track-origins
```

Runtime knobs:

```bash
export ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:strict_string_checks=1
export UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1
export TSAN_OPTIONS=second_deadlock_stack=1
```

Cost: ASan ~2× time and ~3× memory; UBSan near-free for the arithmetic checks;
TSan ~5–15× and ~5× memory. Run the test suite under ASan+UBSan in CI; it costs
minutes and finds the bugs that otherwise cost days.

Complementary tools: `valgrind --tool=memcheck` (slower, no rebuild needed, and
still better at uninitialized reads on GCC builds), `-D_GLIBCXX_ASSERTIONS` /
`-D_LIBCPP_HARDENING_MODE=...` for bounds-checked standard containers in debug
builds, and `-ftrapv`/`-fwrapv` to trap or define signed overflow.

Hardening for release builds worth having on by default:
`-D_FORTIFY_SOURCE=3 -fstack-protector-strong -Wl,-z,relro,-z,now`.

## 5. Warnings that are really UB detectors

```
-Wall -Wextra -Wpedantic
-Wshadow -Wconversion -Wsign-conversion
-Wnon-virtual-dtor -Wold-style-cast -Woverloaded-virtual
-Wnull-dereference -Wdouble-promotion -Wformat=2
-Wcast-align -Wuseless-cast (GCC) -Wdangling-gsl (clang)
```

`-Werror` in CI, not on developer machines (a new compiler version should not
block local work). MSVC equivalent: `/W4 /permissive- /analyze`.

## 6. Reading the disassembly when you suspect UB

If a check "disappears", confirm rather than guess: build the TU with
`-O2 -S -masm=intel` or paste into Compiler Explorer, and diff `-O0` vs `-O2`
behavior. A bug that only reproduces at `-O2`, only with GCC, or only in release
is UB until proven otherwise — not a compiler bug. (Compiler bugs exist; they are
maybe 1 in 100 of the cases where they are blamed.)

## Gotchas

- "It works on my machine at `-O0`" is the classic signature of UB, not evidence
  against it.
- Signed overflow UB is why `for (int i = 0; i <= n; ++i)` with `n == INT_MAX`
  loops forever — the compiler proves `i` never overflows and drops the exit test.
- `unsigned` arithmetic is defined but treacherous: `v.size() - 1` on an empty
  vector is a gigantic positive number, and `i >= 0` is always true for unsigned.
- Strict aliasing bites hardest in serialization code. Use `memcpy`/`bit_cast`;
  the optimizer removes it. `-fno-strict-aliasing` is a workaround, not a fix.
- `memcpy(dst, nullptr, 0)` is UB even with size 0. Same for null iterators into
  `std::copy`.
- `std::vector` reallocation invalidates every iterator, pointer, and reference —
  a `push_back` inside a loop over the same vector is UB with no diagnostic.
- ASan does not find _all_ memory bugs, notably intra-object overflows (one
  struct member into the next) unless you enable
  `-fsanitize-address-field-padding`.
- UBSan is not a substitute for tests: it only reports UB that actually executes.
