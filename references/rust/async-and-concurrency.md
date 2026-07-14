---
topic_id: "v2:OMOK"
topic_path: "rust-arkit/rust-async"
semantic_id: "urRuzaZ578T7mxDgNIRyUfgpM1BJIAAE"
related_ids:
  - "mNh7HTZN7Sx7lhTsrrZSUeipcjxoYAAN"
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
---
# Async and concurrency

Source:

- https://rust-lang.github.io/async-book/ (Asynchronous Programming in Rust)
- https://tokio.rs/tokio/tutorial (Tokio tutorial: spawning, channels, select, bridging sync)
- https://doc.rust-lang.org/std/thread/ (std threads, scoped threads)

## 1. `async fn` is lazy

An `async fn` desugars to a normal function returning an `impl Future`. Calling it does **nothing**: no code in the body runs until the future is polled, which in practice means `.await`ed or handed to a runtime.

```rust
async fn say_hello() { println!("hello"); }

let fut = say_hello();   // prints nothing, allocates a state machine
fut.await;               // NOW it runs
```

The compiler turns the body into a state machine that yields back to the executor at every `.await`. This is cooperative scheduling: a task that never awaits never yields.

## 2. Runtimes: why tokio

Rust ships the `Future` trait but **no runtime**. You pick one; tokio is the ecosystem default (axum, reqwest, sqlx, tonic all build on it).

```rust
#[tokio::main]                    // expands to Runtime::new().block_on(async { ... })
async fn main() {
    let handle = tokio::spawn(async {
        42
    });
    let n = handle.await.unwrap(); // JoinHandle yields Result<T, JoinError>
}
```

`tokio::spawn` requires the future to be `Send + 'static` (and its output `Send + 'static`) because the multi-threaded scheduler can move a task between worker threads at any `.await` point. Borrowed data can't cross into a spawned task; move owned data in (`Arc` for sharing). For `!Send` tasks there is `tokio::task::LocalSet`, and `#[tokio::main(flavor = "current_thread")]` runs everything on one thread.

**Tasks vs threads:** a task is a few hundred bytes of state machine, scheduled cooperatively in user space; a thread is an OS resource with a stack measured in kilobytes-to-megabytes. Spawning 100k tasks is normal; 100k threads is not.

## 3. Channels (tokio::sync)

| Channel     | Shape                                                                 | Use                                                                |
| ----------- | --------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `mpsc`      | many producers, one consumer, bounded or unbounded                    | work queues, actor inboxes                                         |
| `oneshot`   | one value, once                                                       | request/response, "give me the result back"                        |
| `broadcast` | many producers, many consumers, every receiver sees every value       | fan-out events; slow receivers **lag** and get `RecvError::Lagged` |
| `watch`     | one producer, many consumers, receivers see only the **latest** value | config updates, shutdown flags                                     |

Bounded `mpsc::channel(n)` gives backpressure: `send().await` waits when full. `unbounded_channel` never blocks the sender, which means memory is your backpressure.

## 4. `select!` and cancellation

```rust
tokio::select! {
    res = do_work() => handle(res),
    _ = tokio::time::sleep(Duration::from_secs(5)) => println!("timeout"),
}
```

`select!` polls all branches; when one completes, the others are **dropped**, which cancels them. This is where "cancellation safety" matters: a future dropped mid-operation must not lose data. `mpsc::Receiver::recv` is cancel-safe; a half-completed `read_exact` is not. The tokio docs mark each API's cancel safety; check before putting it in a `select!` loop.

## 5. Blocking work

Never block a runtime worker thread: `std::thread::sleep`, synchronous file IO, or a long CPU crunch stalls every task scheduled on that worker.

```rust
let digest = tokio::task::spawn_blocking(move || {
    expensive_hash(&big_buffer)          // runs on a dedicated blocking pool
}).await.unwrap();
```

Use `tokio::time::sleep` (not `std::thread::sleep`), `tokio::fs` (which is `spawn_blocking` under the hood), and `spawn_blocking` for CPU-bound or legacy-blocking calls. For serious data parallelism, hand off to rayon and bridge back with a `oneshot`.

## 6. Locks across `.await`

Holding a `std::sync::MutexGuard` across an `.await` is the classic bug: the guard is `!Send`, so `tokio::spawn` refuses to compile it (a helpful error); on a current-thread runtime it can deadlock instead. Two fixes:

- Scope the guard so it drops before the `.await` (preferred; std Mutex is fine for short critical sections inside async code).
- Use `tokio::sync::Mutex` only when you genuinely must hold the lock across an await point (it is slower and usually a design smell).

## 7. Async in traits

History: `async fn` in traits didn't compile for years; everyone used the `async-trait` crate (which boxes the returned future). Since Rust 1.75, **native `async fn` in traits works** for generic/impl usage. The remaining hole: traits with async methods are not dyn-compatible, so `Box<dyn MyAsyncTrait>` still needs `async-trait` or hand-written `Box<dyn Future>` returns. Libraries that need object safety keep using `async-trait`; everything else can go native.

## 8. Plain threads, scoped threads, rayon

```rust
// std::thread::scope (stable since 1.63): borrow non-'static data safely
let mut counts = vec![0; 4];
std::thread::scope(|s| {
    for c in counts.chunks_mut(1) {
        s.spawn(|| c[0] += 1);   // borrows locals; scope joins all threads on exit
    }
});
```

For data parallelism, skip manual threads entirely:

```rust
use rayon::prelude::*;
let sum: u64 = data.par_iter().map(|x| expensive(x)).sum();
```

Rayon owns a work-stealing thread pool; it is for CPU-bound batch work, not IO. Don't call `par_iter` directly inside an async task (it blocks the worker); wrap it in `spawn_blocking`. Crossbeam supplies the lower-level toolkit: `crossbeam::channel` (fast sync MPMC), epoch GC, lock-free structures.

## 9. What Send and Sync actually mean

- `Send`: ownership of the value can move to another thread.
- `Sync`: `&T` is `Send`, i.e. threads may share references to it concurrently.

Both are auto traits: the compiler derives them structurally, and unsafe code can opt in/out manually. `Rc<T>` is `!Send` (non-atomic refcount), `RefCell<T>` is `!Sync` (non-atomic borrow flags); their thread-safe siblings are `Arc<T>` and `Mutex<T>`/`RwLock<T>`. These bounds are why `tokio::spawn` errors name types you never wrote: some `!Send` value is alive across an `.await`.

## Gotchas

- A future you build but never `.await` (or spawn) is a silent no-op. Clippy's `unused_must_use` on `Future` catches most cases; closures returning futures can still slip through.
- Dropping a tokio `JoinHandle` does **not** cancel the task; it detaches and keeps running. Cancel explicitly with `handle.abort()` or a `CancellationToken` (tokio-util).
- `select!` drops the losing branches every iteration. In a loop, non-cancel-safe futures lose buffered data; hoist the future out of the loop and poll `&mut fut` instead.
- `broadcast` receivers that fall behind get `Lagged(n)` and silently miss n messages; `watch` receivers only ever see the latest value. Neither is a durable queue.
- Async recursion needs indirection: `Box::pin(self.recurse())`, because the state machine would otherwise be infinitely sized.
- The `!Send`-guard-across-await error only fires when something requires `Send` (like `tokio::spawn`). Inside `block_on` or a `LocalSet` the same code compiles and can still deadlock at runtime.
- CPU-bound loops without awaits starve the cooperative scheduler even on the multi-thread runtime; sprinkle `tokio::task::yield_now().await` or move to `spawn_blocking`/rayon.
- Mixing runtimes (a future from async-std polled under tokio, or a tokio API used with no runtime "reactor") panics with "there is no reactor running"; keep the stack single-runtime.
