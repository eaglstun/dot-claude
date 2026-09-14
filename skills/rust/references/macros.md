---
semantic_id: "-Jg7WDZP7KT6N76IKqWbEbkrFhFpIAAN"
related_ids:
  - "nPDrGXZ47LT6kp2oDKWyUalrUlSpIAAF"
  - "mNh7HTZN7Sx7lhTsrrZSUeipcjxoYAAN"
---
# Macros

Source:

- <https://doc.rust-lang.org/book/ch20-05-macros.html> (overview, both kinds)
- <https://doc.rust-lang.org/reference/macros-by-example.html> (macro_rules grammar, fragments, follow sets)
- <https://doc.rust-lang.org/reference/procedural-macros.html> (the three proc-macro kinds)
- <https://veykril.github.io/tlborm/> (The Little Book of Rust Macros)
- <https://docs.rs/syn/latest/syn/> and <https://docs.rs/quote/latest/quote/>

## 1. Which kind

**`macro_rules!`** (declarative) matches token patterns and substitutes. No extra crate,
no compile-time cost, no dependencies. Reach for it for variadic helpers, boilerplate
`impl` blocks, and small DSLs.

**Procedural macros** are Rust programs that take a `TokenStream` and return one. They can
parse, inspect, and generate arbitrary code, and they need their own crate plus `syn` and
`quote`. Reach for them when you need to read a struct's fields (any `#[derive]`), or emit
identifiers derived from input names.

The dividing line in practice: `macro_rules!` cannot construct a new identifier by
concatenation. The moment you want `FooBuilder` from `Foo`, you need a proc macro (or the
`paste` crate, which is a proc macro wearing a hat).

## 2. macro_rules!

```rust
#[macro_export]
macro_rules! hashmap {
    () => { ::std::collections::HashMap::new() };
    ($($k:expr => $v:expr),+ $(,)?) => {{
        let mut m = ::std::collections::HashMap::new();
        $( m.insert($k, $v); )+
        m
    }};
}
```

Repetition is `$( ... ) sep rep` where `rep` is `*` (zero or more), `+` (one or more), or
`?` (zero or one, no separator allowed). The trailing `$(,)?` is how you accept an optional
trailing comma, and you want it on every list-shaped macro.

Fragment specifiers:

| fragment   | matches                         | notes                                                               |
| ---------- | ------------------------------- | ------------------------------------------------------------------- |
| `expr`     | an expression                   | opaque afterwards, see gotchas                                      |
| `ty`       | a type                          |                                                                     |
| `pat`      | a pattern, or-patterns included | `pat_param` is the older form that stops at a top-level alternation |
| `ident`    | an identifier or keyword        |                                                                     |
| `path`     | `a::b::C<T>`                    |                                                                     |
| `literal`  | a literal, with optional `-`    |                                                                     |
| `block`    | `{ ... }`                       |                                                                     |
| `stmt`     | a statement, no trailing `;`    |                                                                     |
| `item`     | fn/struct/impl/use/...          |                                                                     |
| `meta`     | the inside of an attribute      |                                                                     |
| `vis`      | `pub`, `pub(crate)`, or nothing | can match empty                                                     |
| `lifetime` | `'a`                            |                                                                     |
| `tt`       | one token tree                  | the escape hatch, always re-matchable                               |

Always write `::std::...` and `$crate::...` inside a macro body. `$crate` expands to the
defining crate, which is what makes an exported macro work in a caller that has not
imported anything.

**Hygiene**: identifiers _you_ introduce in the macro body are in a distinct syntax
context and cannot collide with or be seen by the caller's locals. This applies to local
variables and lifetimes. It does **not** apply to items, types, or macro names, which is
why the `::` and `$crate` prefixes matter.

**Scope**: `macro_rules!` is textually ordered. A macro is usable after its definition in
the same file, and in modules declared after it. Escape that with `#[macro_export]` (which
hoists it to the crate root, path `mycrate::the_macro`) or by `use crate::the_macro;`.

Debugging: `cargo expand` (from `cargo-expand`) is the whole toolkit. `trace_macros!(true)`
and `-Zmacro-backtrace` on nightly help with recursion.

## 3. Procedural macros

They live in a dedicated crate:

```toml
[lib]
proc-macro = true

[dependencies]
syn = { version = "2", features = ["full"] }
quote = "1"
proc-macro2 = "1"
```

Three kinds:

```rust
#[proc_macro_derive(Builder, attributes(builder))]   // #[derive(Builder)] + #[builder(...)]
pub fn derive_builder(input: TokenStream) -> TokenStream { ... }

#[proc_macro_attribute]                              // #[instrument] fn f() {}
pub fn instrument(attr: TokenStream, item: TokenStream) -> TokenStream { ... }

#[proc_macro]                                        // sql!( ... )
pub fn sql(input: TokenStream) -> TokenStream { ... }
```

The standard shape of a derive:

```rust
#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let ast = syn::parse_macro_input!(input as syn::DeriveInput);
    let name = &ast.ident;
    let builder = syn::Ident::new(&format!("{name}Builder"), name.span());
    let (imp, ty, wher) = ast.generics.split_for_impl();   // handles generics correctly

    quote::quote! {
        impl #imp #name #ty #wher {
            pub fn builder() -> #builder { #builder::default() }
        }
    }
    .into()
}
```

Key differences from declarative macros:

- A **derive** cannot modify the item it is applied to. It only _appends_ new items. An
  **attribute** macro receives the item and returns whatever it likes, including a
  rewritten version, which is how `#[tokio::main]` works.
- Errors: never `panic!`. Return `syn::Error::new_spanned(&field, "message").to_compile_error().into()`
  so the squiggle lands on the offending token instead of on the macro invocation.
- `split_for_impl()` is not optional if the input can be generic. Hand-rolling
  `impl<T> ... where` is how derives break on lifetimes and const params.
- `darling` parses helper attributes declaratively and saves a lot of `syn::Meta` walking.

## 4. When not to write one

A macro is a second language with no type checking, no IDE completion, no rustdoc, and
error messages that point at the expansion. Before writing one, check whether a generic
function, a trait with a blanket impl, a builder, or a plain `const` array of data would
do the same job. The good uses cluster in one place: eliminating boilerplate that the type
system genuinely cannot express, such as per-field code (`serde`, `clap`) or variadics
(`vec!`, `println!`).

Compile-time cost is real. `syn` with `features = ["full"]` is a meaningful chunk of a
cold build, and every derive re-runs per type.

## Gotchas

- **An `expr` (or `ty`, `pat`, `stmt`, `path`, `block`) fragment becomes a single opaque
  token after matching.** You cannot pass it to another rule that tries to match its
  internals, and the failure looks like "no rules expected this token". Capture as `tt`
  and re-parse (TT-muncher) when you need to inspect it later.
- The **follow set** rules restrict what token may come after a fragment: `expr` may only
  be followed by `=>`, `,`, or `;`. `$x:expr $y:expr` does not compile no matter how you
  phrase it.
- Hygiene means a macro **cannot** introduce a variable the caller can then use, and cannot
  see a caller local it did not receive as an argument. Macros that "declare `let result`
  for you" are impossible by design.
- Forgetting `$crate` or `::std` makes a macro that works in its own crate and breaks in
  every consumer, sometimes silently by resolving to the caller's shadowing type.
- `#[macro_export]` ignores module structure: the macro is at the crate root. Re-exporting
  it from a nicer path requires `pub use crate::the_macro;` and, for rustdoc,
  `#[doc(hidden)]` on the root one.
- Recursion limit is 128; deep TT-munchers need `#![recursion_limit = "256"]` at the crate
  root, and the resulting compile times are the real message.
- **Macros expand before type checking**, so a macro can never branch on a type. Anything
  that needs "if `T` implements `Display`" is a trait problem, not a macro problem
  (specialisation is unstable).
- A `proc-macro = true` crate can export _only_ proc macros. Shared helper code must live
  in a separate normal crate that both depend on.
- Proc macros run with the compiler's own dependencies at _build_ time, so they cannot see
  the target when cross-compiling, and `cfg!(target_os)` inside a proc macro reports the
  **host**. Emit `#[cfg(...)]` into the output instead of branching at expansion time.
- Two derives cannot coordinate. Each sees only the item; ordering between them is not
  something you can rely on.
- `macro_rules!` matchers are tried **in order** and the first match wins, so a general
  rule placed above a specific one silently shadows it.
