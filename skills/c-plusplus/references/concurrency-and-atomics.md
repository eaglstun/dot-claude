---
semantic_id: "4YIJRq9ryfq3OsxCricZQ_QrtRhKAAAK"
related_ids:
  - "IQ45VK5BgTq3ssTGrmMbZ_wloZxQQAAI"
  - "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
---
# Concurrency, atomics, and the memory model

Source:

- https://en.cppreference.com/w/cpp/thread
- https://en.cppreference.com/w/cpp/atomic/memory_order
- https://en.cppreference.com/w/cpp/thread/jthread
- https://en.cppreference.com/w/cpp/thread/condition_variable
- https://en.cppreference.com/w/cpp/atomic/atomic
- https://en.cppreference.com/w/cpp/thread/latch (latch/barrier/semaphore, C++20)

## 1. Threads

```cpp
std::jthread t{[](std::stop_token st, int n) {          // C++20: joins on destruction
    while (!st.stop_requested()) work(n);
}, 42};
t.request_stop();                                        // cooperative cancellation
// destructor calls request_stop() then join()

std::thread raw{f};                                      // C++11: MUST join() or detach()
raw.join();                                              // else ~thread calls std::terminate
```

Use `std::jthread` everywhere it exists. `std::thread`'s destructor terminating
on a non-joined thread has caused more outages than it has prevented.

`std::thread::hardware_concurrency()` is a _hint_ (may return 0, ignores cgroup
limits and affinity). For a real thread pool, read the affinity mask or the
container's CPU quota.

An exception escaping a thread function calls `std::terminate`. Wrap the body,
or use `std::async`/`packaged_task` which capture it into the future.

## 2. Mutexes and locks

```cpp
std::mutex m;
{
    std::lock_guard lk{m};                 // simplest; no unlock, no condition variable
}
{
    std::unique_lock lk{m};                // movable, deferrable, works with condition_variable
    cv.wait(lk, [&]{ return ready; });
}
{
    std::scoped_lock lk{m1, m2};           // C++17: multiple mutexes, deadlock-free ordering
}
{
    std::shared_lock lk{rw};               // many readers
    // std::unique_lock lk{rw};            // one writer, on a std::shared_mutex
}
```

- Never call `lock()`/`unlock()` by hand — an early return or a throw leaks the lock.
- `std::scoped_lock` (not `lock_guard`) for two or more mutexes; it uses a
  deadlock-avoidance algorithm. Otherwise: **always acquire in a documented
  global order**.
- `std::recursive_mutex` is almost always a design smell (it means you don't know
  what your invariants are).
- `std::shared_mutex` only pays off when reads vastly outnumber writes _and_ the
  critical section is long; otherwise a plain mutex wins on cache traffic.
- `std::call_once` + `std::once_flag` for one-time init — or just use a function-
  local `static`, which is already thread-safe.
- Hold locks for the shortest possible region, and **never call user code or
  block on I/O while holding one**.

## 3. Condition variables

```cpp
std::mutex m; std::condition_variable cv; std::queue<Job> q; bool done = false;

// producer
{ std::lock_guard lk{m}; q.push(job); }
cv.notify_one();

// consumer
std::unique_lock lk{m};
cv.wait(lk, [&]{ return !q.empty() || done; });      // predicate form: handles spurious wakeups
```

**Always use the predicate overload.** Spurious wakeups are real, and a bare
`wait()` also races with a notify that arrives before you wait. The state must be
protected by the same mutex you pass to `wait`.

`notify_one` vs `notify_all`: one when any single waiter can make progress, all
when the state change may satisfy different predicates. Notify _after_ releasing
the lock when you can, to avoid the woken thread immediately blocking.

C++20 adds `std::counting_semaphore`/`binary_semaphore`, `std::latch`
(single-use countdown), `std::barrier` (reusable phase sync), and
`std::atomic<T>::wait`/`notify_one` (futex-backed, no mutex needed) — often
simpler and faster than a condvar for a single flag.

## 4. Futures

```cpp
std::future<int> f = std::async(std::launch::async, compute, arg);
int result = f.get();                                 // blocks; rethrows the callee's exception

std::promise<int> p; auto fut = p.get_future();
std::jthread t{[&p]{ p.set_value(42); }};             // or p.set_exception(std::current_exception())
```

`std::async` **without** an explicit launch policy may run lazily on `get()` —
always pass `std::launch::async` if you want a thread. And the returned future's
destructor _blocks_ until the task finishes (only for `async`-launched ones),
which turns `std::async(f); std::async(g);` into sequential execution.

The C++11 future/promise API has no continuations, no `when_all`, no
cancellation. Real async work belongs in `std::execution` (senders/receivers,
C++26), or today in Asio, libunifex, stdexec, Folly, or TBB.

## 5. Atomics and memory order

```cpp
std::atomic<int> counter{0};
counter.fetch_add(1, std::memory_order_relaxed);       // statistics: no ordering needed
int expected = 0;
counter.compare_exchange_weak(expected, 1, std::memory_order_acq_rel,
                                            std::memory_order_acquire);
std::atomic<bool> ready{false};
std::atomic_flag spin = ATOMIC_FLAG_INIT;
```

| Order     | Guarantee                                                 |
| --------- | --------------------------------------------------------- |
| `relaxed` | atomicity only; no ordering with other operations         |
| `consume` | do not use — every compiler promotes it to `acquire`      |
| `acquire` | on a load: no later read/write moves before it            |
| `release` | on a store: no earlier read/write moves after it          |
| `acq_rel` | both, for read-modify-write                               |
| `seq_cst` | total global order across all `seq_cst` ops (the default) |

The **release/acquire pair** is the workhorse: a release store of a flag makes
everything the writer did _before_ it visible to any reader that acquire-loads
the same flag.

```cpp
// producer                              // consumer
data = compute();                        if (ready.load(std::memory_order_acquire))
ready.store(true, std::memory_order_release);   use(data);   // guaranteed to see the write
```

`seq_cst` is the safe default and costs a full barrier (`mfence`/`dmb ish`) —
noticeable in hot loops, invisible elsewhere. Relaxing memory order is an
optimization to make **after** measuring, with a very careful argument.

`std::atomic<T>` for a non-trivially-copyable or oversized `T` is lock-based
internally — check `is_lock_free()` / `is_always_lock_free`. `std::atomic<double>`
has no atomic arithmetic before C++20 (`fetch_add` on floats landed then).

**A data race is UB**, not "a stale read". Two threads touching the same
non-atomic object with at least one write, without synchronization, poisons the
whole program. `volatile` does **not** make anything thread-safe — it is for
memory-mapped I/O and signal handlers only.

## 6. False sharing and layout

Two atomics in the same cache line ping-pong between cores at ~100× the cost of
uncontended access:

```cpp
struct alignas(std::hardware_destructive_interference_size) Counter {
    std::atomic<std::uint64_t> value{0};
};
std::array<Counter, kThreads> counters;    // one per core, summed at the end
```

(`hardware_destructive_interference_size` is 64 on x86-64, 128 on Apple silicon /
some ARM; libstdc++ warns about ABI stability when you use it — a hardcoded 64
with a comment is acceptable and common.)

## 7. Parallel algorithms

```cpp
#include <execution>
std::sort(std::execution::par, v.begin(), v.end());
auto total = std::transform_reduce(std::execution::par_unseq,
                                   v.begin(), v.end(), 0.0, std::plus{}, to_weight);
```

`seq` / `unseq` (vectorize) / `par` (threads) / `par_unseq` (both). The callable
must not throw (`terminate` if it does), must not lock (with `unseq`, which may
interleave calls in one thread), and needs enough work per element to beat the
scheduling overhead. libstdc++ requires TBB (`-ltbb`); check availability before
depending on it.

## 8. TSan and testing concurrency

```bash
-fsanitize=thread -g -O1     # ~5-15x slower, finds races that never manifested
```

Run the whole test suite under TSan in CI. Races are timing-dependent and will
not reproduce on demand; the sanitizer finds them from a single non-racing run
because it tracks happens-before, not accidental interleavings.

## Gotchas

- `std::thread` destructor without join/detach → `std::terminate`. Use `jthread`.
- `std::async` without `std::launch::async` may never start a thread; and the
  returned future's destructor blocks, silently serializing your parallelism.
- `cv.wait` without a predicate loses notifications and wakes spuriously.
- `notify` without holding (or having held) the mutex around the state change is
  a lost-wakeup race.
- Locking two mutexes in different orders in two functions = deadlock, found in
  production at 3am. Use `scoped_lock` or a fixed order.
- `volatile` is not atomic, not a barrier, and not thread-safe.
- `shared_ptr`'s control block is atomic; the pointee and the `shared_ptr`
  variable itself are not.
- A `const` member function is not automatically thread-safe — `const` means
  "logically immutable", and `mutable` members break it outright.
- Reference-counting, lazy caching in `const` getters, and copy-on-write are the
  three most common accidental race sources in "read-only" code.
- Thread-per-request scales badly past a few hundred; use a bounded pool.
- `std::atomic<T>::wait/notify` (C++20) is usually faster than a condvar for a
  single boolean, with far less code.
