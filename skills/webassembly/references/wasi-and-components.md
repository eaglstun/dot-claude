# WASI and the Component Model

Sources:

- https://wasi.dev/
- https://github.com/WebAssembly/WASI
- https://component-model.bytecodealliance.org/
- https://component-model.bytecodealliance.org/design/wit.html
- https://component-model.bytecodealliance.org/advanced/canonical-abi.html
- https://component-model.bytecodealliance.org/reference/faq.html

## 1. Four things commonly called “Wasm”

- A **core module** has low-level numeric/reference imports and exports.
- A **WASI Preview 1 module** is a core module importing legacy `wasi_snapshot_preview1`
  functions, commonly as a command or reactor.
- A **component** uses Component Model types and canonical ABI lowering/lifting,
  often wrapping one or more core modules.
- A **WASI component** imports standardized WASI interfaces expressed in WIT.

Do not feed one artifact kind to a host mode expecting another without an
adapter/componentization step.

## 2. Capabilities, not an emulated operating system

WASI APIs are host-provided interfaces. The runtime decides which directories,
environment values, clocks, random sources, sockets, or HTTP capabilities a
guest receives. Preopened directories are scoped capabilities, not evidence the
guest can traverse the host filesystem.

Preview 1 is widespread legacy ABI. WASI 0.2 (“Preview 2”) is Component
Model/WIT based. WASI 0.3 adds native async functions, streams and futures and
changes interface shapes. Toolchain/runtime support differs, so name the exact
target rather than saying “WASI” alone.

## 3. WIT

WIT declares packages, interfaces, worlds, types, imports, and exports. Its
value types include records, variants, enums, flags, options, results, lists,
tuples, resources, and (in newer versions) async/stream/future forms. A world is
the full contract for a component.

```wit
package example:greeter;

interface greet {
  hello: func(name: string) -> result<string, string>;
}

world service {
  export greet;
}
```

Generated bindings lower rich values to core Wasm through the canonical ABI and
manage language-specific representations. Resource handles express identity and
lifetime without exposing raw guest pointers.

## 4. Composition and adapters

Components can be composed when imports and exports match. Adapters can bridge
legacy Preview 1 modules to component-era WASI contracts, but they do not make
every arbitrary C ABI interoperable. Inspect with `wasm-tools component wit` and
validate with the matching feature set.

## Gotchas

- “Preview 1 component” is usually a legacy core module, not a Component Model
  component.
- WASI does not grant filesystem/network access by default; the host does.
- WIT type compatibility is structural/nominal according to Component Model
  rules, not “these two language structs look alike.”
- WASI 0.2 and 0.3 async interfaces are not interchangeable source APIs.
- Adapters add compatibility, not ambient authority.

