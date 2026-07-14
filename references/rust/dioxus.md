---
topic_id: "v2:OJBE"
topic_path: "rust-arkit/rust-fundamentals"
semantic_id: "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
related_ids:
  - "HbA7Gddd68D7J5T4OpWSU2nbdVVpcAAO"
  - "KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"
---
# Dioxus

Source:

- https://dioxuslabs.com (project home)
- https://dioxuslabs.com/learn/0.7/ (0.7 docs: tutorial, essentials, guides)
- https://dioxuslabs.com/learn/0.7/getting_started/ (dx CLI install, platform setup)
- https://dioxuslabs.com/learn/0.7/essentials/fullstack/server_functions (server functions)

## 1. What it is

Dioxus is a Rust framework for building **fullstack web, desktop, and mobile apps from one codebase**. The mental model is React, transplanted: components are functions returning `Element`, UI is declared in an HTML-ish macro (`rsx!` instead of JSX), state lives in hooks and signals, and the renderer diffs and patches. If you know React, the concepts map one-to-one; the payoff is that frontend, backend, and shared types are all Rust, checked by one compiler. Current stable line: **0.7**.

## 2. Components and rsx!

A component is a function returning `Element`, marked `#[component]` (which generates the props struct from the parameters):

```rust
use dioxus::prelude::*;

#[component]
fn DogApp(breed: String) -> Element {
    rsx! {
        h1 { "Breed: {breed}" }
    }
}

#[component]
fn App() -> Element {
    rsx! {
        Header {}
        DogApp { breed: "corgi" }   // props passed like attributes
        Footer {}
    }
}
```

`rsx!` takes element names, `attribute: value` pairs, child blocks, and `"{interpolated}"` strings. Components are memoized by default: they re-render only when props change or state they read changes. Library authors can hand-write a `#[derive(Props, PartialEq, Clone)]` struct instead of using `#[component]`.

## 3. State: hooks and signals

`use_signal` creates a `Signal<T>`, a tracked wrapper: reads subscribe the component, writes re-render exactly the subscribers.

```rust
#[component]
fn Counter() -> Element {
    let mut count = use_signal(|| 0);

    rsx! {
        button {
            onclick: move |_| count += 1,     // event handler: a move closure
            "count is {count}"                // read via display interpolation
        }
    }
}
```

Reading: call syntax `count()` clones the value, `.read()` borrows it. Writing: `.set(v)`, `.write()` for a mutable borrow, or operators like `+=`. Signals are `Copy` (they are keys into arena storage), so closures capture them freely without `Rc` gymnastics.

- `use_effect(move || { ... })` runs after render and re-runs when signals it reads change (side effects: DOM/eval, logging, syncing).
- `use_resource(move || async move { ... })` ties state to async work (fetching); read it with `.cloned()` / match on `Some`/`None`, restart with `.restart()`; integrates with Suspense and SSR streaming.
- `use_context_provider` / `use_context` share state down the tree without prop drilling.
- Hook rules are React's: call hooks unconditionally, at the top of the component, never in loops/branches.

## 4. The dx CLI

```bash
curl -sSL https://dioxus.dev/install.sh | bash   # recommended prebuilt binary
cargo binstall dioxus-cli --force                # or via binstall
cargo install dioxus-cli                         # from source (slow, ~10 min)

dx new my-app        # interactive template: pick platforms, styling, router
dx serve             # dev server with hot reloading
dx serve --platform desktop
dx bundle            # release bundles (installers, wasm bundle, etc.)
```

`dx serve` hot-reloads `rsx!` markup and assets instantly, and 0.7 added experimental **hot-patching of Rust code itself** (subsecond rebuilds of changed functions), which is the headline dev-experience feature of the release.

## 5. Render targets

One component tree, four deployment shapes:

- **Web**: compiled to WebAssembly, rendered against the real DOM (plus SSR/hydration in fullstack mode).
- **Desktop**: your Rust runs natively and renders into a system **webview** (via wry/tao, the same engine family Tauri uses); no JS frontend involved.
- **Mobile**: iOS and Android via the same webview approach; `dx` handles the platform scaffolding. Newest and roughest of the targets.
- **Fullstack**: server + client from one crate. Server functions are async fns that compile into an HTTP endpoint on the server and an RPC stub on the client:

```rust
#[get("/api/hello-world")]           // 0.7: HTTP-method macros; #[server] = anonymous route
async fn hello_world() -> Result<String> {
    Ok("Hello world!".to_string())
}

// client side: just call it
let onclick = move |_| async move {
    let msg = hello_world().await;
};
```

0.7's `Result` here is a re-export of `anyhow::Result`; errors downcast to `ServerFnError` on the client, and extractors (Axum `FromRequestParts`) can be pulled in via the macro (`#[post("/api/login", auth: auth::Session)]`). The server side rides on axum, so custom routes/middleware slot in.

## 6. How it differs from the neighbors

- **vs Tauri**: both use a system webview for desktop, but in Tauri the UI is a **JavaScript frontend** (React/Svelte/...) with Rust as the backend over IPC; in Dioxus the UI itself is **Rust code**. Pick Tauri to reuse a web team/app; pick Dioxus for all-Rust.
- **vs Leptos/Yew**: those are **web-first** (wasm in the browser, Leptos with strong SSR). Dioxus covers web too, but its distinguishing bet is **multi-platform**: the same components run as desktop and mobile apps. Leptos's fine-grained reactivity and Dioxus's signals are similar in spirit; Yew is the older React-alike.
- **vs egui**: egui is immediate-mode (great for tools/debug UIs); Dioxus is retained, styled with real CSS, and app-shaped.

## 7. Maturity, honestly

Dioxus is the most credible all-Rust app story right now, with real funding and a fast-moving team, but it is **0.x software**: every minor release (0.5, 0.6, 0.7) has broken APIs, and 0.7 itself reshaped the server-function attributes (HTTP-method macros replacing the old bare `#[server]` style) and reworked the docs. Expect churn in examples/blog posts that target older versions, an ecosystem of third-party components far thinner than React's, and webview quirks that differ per OS. Pin your `dioxus` version, read the migration guide when bumping, and treat mobile as the least-baked target.

## Gotchas

- Version skew is the number-one confusion: 0.4/0.5-era snippets (`cx: Scope`, `use_state`, `render!`) do not compile on 0.6/0.7. Modern code has no `Scope`/`cx`: components take props directly and use `use_signal`. Check which version a tutorial targets before copying.
- Signals are `Copy` handles, not the value: `let c = count;` copies the handle (both point at the same state). Use `count()` or `.read()` to get at the value; comparing or printing the `Signal` itself is not what you want.
- Holding a `.read()` or `.write()` borrow across another signal write panics at runtime (borrow rules enforced dynamically, like `RefCell`). Keep borrows short; don't stash guards.
- Hook-order violations (hooks in `if`/loops/early-return paths) corrupt hook state and produce confusing panics, exactly like React's rules-of-hooks.
- Server functions must be compiled from a fullstack build (`dx serve` with the fullstack feature/platform); calling one from a plain web build fails at runtime because no server exists and the endpoint was never mounted.
- Building the web target with `cargo build` alone misses the wasm bundling/asset pipeline; use `dx serve` / `dx build` (this is dx's job, the way trunk is for Leptos/Yew).
- Desktop apps render in the OS webview: styling/behavior can differ across WebKit (macOS/Linux) and WebView2 (Windows), and Linux needs the webkit2gtk system packages installed before it will even build/run.
- The rsx hot reload only covers markup/asset edits; changes to arbitrary Rust logic need the (experimental) hot-patch path or a full rebuild. If state seems stale after a big edit, restart `dx serve` before debugging "bugs".
