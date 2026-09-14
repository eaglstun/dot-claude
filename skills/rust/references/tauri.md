---
semantic_id: "nPDrGXZ47LT6kp2oDKWyUalrUlSpIAAF"
related_ids:
  - "lPD-DXbp6RT7h5y4CJExUbg6VkUpIAAH"
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
---
# Tauri

Source:

- <https://v2.tauri.app/start/> (v2 concepts, prerequisites, create-tauri-app)
- <https://v2.tauri.app/develop/calling-rust/> (commands, state, events, channels)
- <https://v2.tauri.app/security/> (capabilities, permissions, CSP)
- <https://v2.tauri.app/plugin/> (the official plugin set)
- <https://v2.tauri.app/start/migrate/from-tauri-1/> (v1 to v2 migration)

## 1. What it is

A desktop and mobile app framework: a Rust backend process plus a UI rendered in the
**operating system's own webview**. No bundled browser engine, which is the whole pitch
against Electron: single-digit-megabyte binaries, a few tens of megabytes of RAM, and a
Rust core you can put real work in.

The cost of that pitch is that you ship against three rendering engines you do not choose:
WKWebView on macOS and iOS, WebView2 (Chromium) on Windows, WebKitGTK on Linux, Android
System WebView on Android. Behaviour differs, especially around media, fonts, and newer
CSS.

v2 (stable since late 2024) added **iOS and Android** targets and replaced the v1 allowlist
with the capabilities/permissions system.

## 2. Layout and CLI

```
my-app/
  src/                    # any frontend: Vite, SvelteKit, Next static export, plain HTML
  src-tauri/
    Cargo.toml
    tauri.conf.json       # windows, bundle, identifier, dev/build commands, CSP
    build.rs
    capabilities/
      default.json        # which windows may call which permissions
    icons/
    src/
      main.rs             # thin: calls lib.rs run()
      lib.rs              # the actual app, so mobile targets can share it
```

```bash
npm create tauri-app@latest        # scaffolds frontend + src-tauri
cargo tauri dev                    # dev server + hot-reloading webview
cargo tauri build                  # release bundle (.app/.dmg, .msi, .deb/.AppImage)
cargo tauri android init && cargo tauri android dev
cargo tauri ios init     && cargo tauri ios dev
cargo tauri info                   # prints the environment; first stop for any build failure
```

Prerequisites are per-platform and non-negotiable: Xcode command line tools on macOS, the
MSVC build tools plus WebView2 on Windows, `libwebkit2gtk-4.1-dev` and friends on Linux,
Android Studio and the NDK for Android.

## 3. Commands: calling Rust from the frontend

```rust
#[tauri::command]
fn greet(name: &str) -> String { format!("Hello, {name}") }

#[tauri::command]
async fn fetch_rows(db: tauri::State<'_, Db>, limit: u32) -> Result<Vec<Row>, String> {
    db.query(limit).await.map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(Db::connect())                       // typed global state
        .invoke_handler(tauri::generate_handler![greet, fetch_rows])
        .run(tauri::generate_context!())
        .expect("error while running tauri app");
}
```

```js
import { invoke } from "@tauri-apps/api/core";
const msg = await invoke("greet", { name: "Ada" }); // camelCase args
const rows = await invoke("fetch_rows", { limit: 50 });
```

Rules that matter:

- Arguments arrive as JSON and are matched by name in **camelCase** by default, while the
  Rust parameter is snake_case. Tauri does that conversion for you; a mismatch is a runtime
  "invalid args" error, not a compile error. Use `#[tauri::command(rename_all = "snake_case")]`
  to turn it off.
- Return type must be `Serialize`. The error type of a returned `Result` must be
  `Serialize` too, so a `thiserror` enum needs a `Serialize` impl (commonly
  `impl Serialize for Error { fn serialize(...) { serializer.serialize_str(&self.to_string()) } }`).
- `async fn` commands run on the async runtime. **Sync commands run on the main thread**, so
  a blocking sync command freezes the UI. Make anything slow `async`, or spawn.
- State: `.manage(T)` once, then `tauri::State<'_, T>` as a parameter. `T` must be
  `Send + Sync + 'static`. Asking for state that was never managed panics at call time.
  Interior mutability (`Mutex`, `RwLock`) is on you.

## 4. Events and channels: Rust to frontend

```rust
use tauri::{Emitter, Listener};
app.emit("progress", 42)?;                       // to all windows
window.emit_to("main", "progress", 42)?;         // to one
```

```js
import { listen } from "@tauri-apps/api/event";
const un = await listen("progress", (e) => setPct(e.payload));
```

For high-frequency or ordered streams (a download, a log tail, model tokens), prefer a
**Channel** over events: it is typed, ordered, and much cheaper per message.

```rust
#[tauri::command]
async fn stream(on_chunk: tauri::ipc::Channel<String>) -> Result<(), String> {
    for c in chunks() { on_chunk.send(c).map_err(|e| e.to_string())?; }
    Ok(())
}
```

Large binary payloads should not go through JSON IPC at all. Use `tauri::ipc::Response`
with raw bytes, or register a custom protocol / local asset URL and let the webview fetch
it.

## 5. Security: capabilities and permissions

v1's global allowlist is gone. In v2, each plugin ships **permissions** (named grants like
`fs:allow-read-text-file`), and your app groups them into **capabilities** scoped to
specific windows:

```json
// src-tauri/capabilities/default.json
{
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "dialog:allow-open",
    {
      "identifier": "fs:allow-read-text-file",
      "allow": [{ "path": "$APPCONFIG/*" }]
    }
  ]
}
```

Also set a real CSP in `tauri.conf.json`; the scaffolded default is `null`, which means no
CSP at all. Your own `#[tauri::command]` functions are **not** covered by permissions unless
you write a plugin, so a command that takes an arbitrary path and reads it has quietly
re-opened everything the capability system was closing. Validate paths in the command.

## 6. Plugins

Most non-trivial capability lives in official plugins rather than the core: `fs`, `dialog`,
`shell`, `http`, `notification`, `clipboard-manager`, `global-shortcut`, `store`,
`sql` (SQLite/Postgres/MySQL), `updater`, `deep-link`, `single-instance`, `window-state`,
`log`, `opener`, `stronghold`. Each is a Rust crate plus a JS package plus permissions to
add:

```bash
cargo tauri add dialog          # adds the crate, the npm package, and the plugin init
```

Sidecars (bundling an external binary, for example a Python or ffmpeg helper) are declared
in `tauri.conf.json` under `bundle.externalBin` with a target-triple-suffixed filename.

## 7. Choosing between Tauri, Dioxus, and Electron

- **Tauri**: web frontend in whatever JS framework you already know, Rust backend, smallest
  binaries, best-supported mobile story of the three, mature bundler/updater/signing.
- **Dioxus desktop**: also a webview, but the UI is written in Rust (`rsx!`), so there is no
  JS toolchain at all. Pick it when you want one language end to end. See `dioxus.md`.
- **Electron**: ships Chromium, so rendering is identical everywhere and the ecosystem is
  enormous, at 100+ MB and a Node backend.

If the app is mostly a UI over Rust compute, Tauri. If it is mostly a web app that needs a
desktop shell and heavy npm integration, weigh Electron honestly.

## Gotchas

- **You are testing three webviews.** A CSS or JS feature that works in dev on macOS may not
  exist in the WebKitGTK build on a user's Debian. Check availability against Safari, not
  Chrome, for macOS/iOS.
- Linux users need `webkit2gtk` installed, and the required version changed between distro
  releases. This is the number one Tauri deployment complaint and it is not something your
  code can fix.
- **v1 to v2 migration is large**: the allowlist became capabilities, `@tauri-apps/api`
  split into per-plugin npm packages, `emit`/`listen` moved onto the `Emitter`/`Listener`
  traits (so you must `use tauri::Emitter;` or the method "does not exist"), and
  `window.__TAURI__` requires `app.withGlobalTauri`. Follow the official migration guide
  rather than patching errors one at a time.
- A command returning `Result<T, E>` where `E` is not `Serialize` fails to compile with a
  message pointing at the `generate_handler!` macro, several layers away from the actual
  function.
- Forgetting to list a command in `generate_handler![]` compiles fine and fails at runtime
  with "command not found".
- `tauri::State<'_, T>` for a type never passed to `.manage()` panics. There is no
  compile-time link between the two.
- Sync commands block the main thread and therefore the UI. If a command does file I/O or
  network work, make it `async` (or `spawn_blocking`), always.
- Hot reload applies to the **frontend** only. Changing Rust triggers a full recompile and
  app restart, so structure the app to keep the Rust surface small during UI iteration.
- Devtools are enabled in dev and disabled in release builds; enable the `devtools` feature
  deliberately if you need them in a release build, and remember shipping that is a
  security decision.
- Auto-updates require a signing keypair generated with `cargo tauri signer generate`, and
  losing the private key means you can never update installed apps again. Back it up
  somewhere you would back up a code-signing certificate.
- macOS distribution outside the App Store still needs Apple Developer ID signing and
  notarisation; Tauri automates the invocation, not the account.
- The default `tauri.conf.json` has `"csp": null`. Ship a real one.
