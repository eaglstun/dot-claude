---
semantic_id: "pQYhxOrrxTr8vshKrGFfcfV7tVvBYAAJ"
related_ids:
  - "JZIhRS7rzjrxCs5K7mDfcfWbiUzIIAAP"
  - "9cIxBb5Zxjq1pt5ArPedc_U_vBnIIAAF"
---
# Coroutines (C++20)

Source:

- https://en.cppreference.com/w/cpp/language/coroutines
- https://en.cppreference.com/w/cpp/coroutine/coroutine_handle
- https://en.cppreference.com/w/cpp/coroutine/generator (C++23 `std::generator`)
- https://lewissbaker.github.io/ (the canonical explainer series)
- https://github.com/lewissbaker/cppcoro / https://github.com/facebookexperimental/libunifex

## 1. What C++20 actually shipped

C++20 shipped the **language mechanism** and almost no library. A function is a
coroutine if its body contains `co_await`, `co_yield`, or `co_return`; the
compiler then rewrites it into a state machine and looks up a
`std::coroutine_traits`/`promise_type` that _you_ (or a library) provide.

So: writing a coroutine is easy, _defining the type it returns_ is the hard part.
Use a library — `std::generator` (C++23), cppcoro, libcoro, Asio's
`awaitable<T>`, folly::coro, or libunifex — unless you are specifically learning
the machinery.

## 2. The three keywords

```cpp
co_await expr;        // suspend until expr's awaiter says to resume
co_yield value;       // == co_await promise.yield_value(value)
co_return value;      // finish, calling promise.return_value/return_void
```

A coroutine cannot use plain `return`, cannot be `constexpr`, cannot be `main`,
a constructor, or a destructor, and cannot be variadic.

## 3. Generators — the easy win

```cpp
std::generator<int> fibonacci() {          // C++23
    int a = 0, b = 1;
    while (true) { co_yield a; std::tie(a, b) = std::pair{b, a + b}; }
}

for (int x : fibonacci() | std::views::take(10)) std::print("{} ", x);
```

`std::generator<Ref, Value>` is a `view`, composes with ranges, and handles
recursive yields via `co_yield std::ranges::elements_of(inner())`. This is the
one coroutine facility most codebases actually need: lazy sequences without
writing an iterator class.

Availability: libstdc++ 14+, MSVC 19.43+; libc++ was still catching up as of
early 2026. `cppcoro::generator` or `__gnu_cxx` equivalents fill the gap.

## 4. The promise_type protocol

If you must write your own return type:

```cpp
template <class T>
struct Task {
    struct promise_type {
        T value_;
        std::exception_ptr err_;

        Task get_return_object() {
            return Task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_always initial_suspend() noexcept { return {}; }  // lazy start
        std::suspend_always final_suspend()   noexcept { return {}; }  // must be noexcept
        void return_value(T v) { value_ = std::move(v); }
        void unhandled_exception() { err_ = std::current_exception(); }
    };

    std::coroutine_handle<promise_type> h_;
    explicit Task(std::coroutine_handle<promise_type> h) : h_(h) {}
    ~Task() { if (h_) h_.destroy(); }                    // YOU own the frame
    Task(Task&& o) noexcept : h_(std::exchange(o.h_, {})) {}
    Task(const Task&) = delete;

    T get() { h_.resume(); if (h_.promise().err_) std::rethrow_exception(h_.promise().err_);
              return std::move(h_.promise().value_); }
};
```

Required members: `get_return_object`, `initial_suspend`, `final_suspend`
(`noexcept`), `unhandled_exception`, and exactly one of `return_void` /
`return_value`. Optional: `yield_value`, `await_transform`,
`operator new`/`delete` (to control frame allocation).

`initial_suspend` returning `suspend_always` = lazy (body runs on first
`resume()`); `suspend_never` = eager (body runs up to the first `co_await` at
call time). Lazy is almost always what you want for a task type.

## 5. Awaiters

`co_await e` needs an awaiter with three members:

```cpp
struct Awaiter {
    bool await_ready() noexcept;                       // true = don't suspend
    // one of:
    void await_suspend(std::coroutine_handle<> h);     // suspend; you store/schedule h
    bool await_suspend(std::coroutine_handle<> h);     // false = resume immediately
    std::coroutine_handle<> await_suspend(std::coroutine_handle<> h);  // symmetric transfer
    T    await_resume();                               // the value of the co_await expression
};
```

The handle-returning form is **symmetric transfer** — it resumes another
coroutine via a tail call instead of nesting, which is what keeps a deep chain of
awaits from overflowing the stack. Any serious task type uses it in
`final_suspend` to resume its continuation.

`std::suspend_always` and `std::suspend_never` are the two trivial awaiters.

## 6. Frame allocation and performance

The coroutine frame (locals live across suspension, the promise, resume/destroy
pointers) is heap-allocated by default. Compilers can elide it (HALO — heap
allocation elision) when the coroutine's lifetime is provably contained in the
caller, typically for a generator consumed inline at `-O2`. Don't count on it
across a translation-unit boundary or through a type-erased task.

To control it: define `operator new`/`operator delete` on the `promise_type`
(e.g. bump-allocate from a per-request arena).

Cost, roughly: a suspend/resume is a handful of ns (an indirect call plus a
switch), far cheaper than a thread context switch, more expensive than a plain
function call. Use them for I/O concurrency and lazy sequences, not to replace
a tight loop.

## 7. Choosing a library

| Need                                    | Reach for                                                     |
| --------------------------------------- | ------------------------------------------------------------- |
| Lazy sequences                          | `std::generator` (C++23), `cppcoro::generator`                |
| Async I/O, networking                   | **Asio** `awaitable<T>` + `co_spawn` — the most battle-tested |
| Structured concurrency, sender/receiver | libunifex / stdexec (the C++26 `std::execution` prototype)    |
| A task type with continuations          | `cppcoro::task`, `folly::coro::Task`                          |
| Nothing — you want to learn             | write the `Task` above, then throw it away                    |

Rolling your own scheduler + task type is a multi-week project with subtle
lifetime bugs. Every team that has done it says so afterwards.

## Gotchas

- **Reference parameters dangle.** Parameters are copied into the frame _by
  value_, but a `const T&` parameter copies the _reference_, and the referent
  may die before the coroutine resumes. Pass by value into coroutines.
  Same for lambdas: a coroutine lambda's captures are **not** stored in the
  frame — the closure must outlive the coroutine.
- Capturing `this` in a member coroutine ties the frame's validity to the
  object's lifetime, with no diagnostic.
- Forgetting `h.destroy()` leaks the frame; calling it twice, or resuming a
  finished coroutine, is UB. `done()` tells you which.
- `final_suspend` must be `noexcept`, and if it returns `suspend_never` the frame
  self-destroys — after which touching the handle (or the promise's result) is
  use-after-free.
- Coroutines and exceptions: an exception escaping the body goes to
  `unhandled_exception()`; if you don't rethrow it somewhere, it vanishes.
- `co_await` inside a `catch` block is allowed; `co_await` in a destructor is not
  usable in practice.
- Debugging is rough: stack traces show the resume frame, not the logical async
  call chain. Log correlation IDs.
- Compiler support diverges on the library side, not the language side — the
  keywords work everywhere (GCC 10+, clang 14+ without `-fcoroutines-ts`,
  MSVC 19.28+), `std::generator` does not.
