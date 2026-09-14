# WAT and binary format

Sources:

- https://webassembly.github.io/spec/core/text/index.html
- https://webassembly.github.io/spec/core/binary/index.html
- https://github.com/WebAssembly/wabt
- https://github.com/WebAssembly/binaryen

## 1. WAT is a representation, not the runtime format

WebAssembly Text Format (`.wat`) is a readable S-expression syntax for core
modules. Engines normally consume the compact binary (`.wasm`). Names such as
`$sum` are conveniences resolved to integer indices; most are absent from the
semantic binary unless preserved in a custom name section.

```wat
(module
  (memory (export "memory") 1)
  (func (export "add") (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    i32.add))
```

Folded `(i32.add (local.get $a) (local.get $b))` and linear stack syntax encode
the same instruction sequence. Prefer linear form when debugging stack effects.

## 2. Binary sections

The binary starts with magic/version bytes, followed by length-delimited
sections. Standard sections include type, import, function, table, memory,
global, export, start, element, code, and data. Their ordering and index-space
rules matter. Integers commonly use unsigned or signed LEB128 variable-length
encoding.

Custom sections may appear in permitted positions and do not affect core
semantics. Common payloads include `name`, producers metadata, DWARF, linking
metadata, and source maps. Stripping custom sections can dramatically reduce a
debug build but removes diagnostic value.

## 3. Inspection loop

Useful commands (exact flags vary by installed version):

```sh
wasm-tools validate module.wasm
wasm-tools print module.wasm
wasm-tools objdump module.wasm
wasm-validate module.wasm
wasm2wat module.wasm
wasm-objdump -x module.wasm
wasm-opt -Oz input.wasm -o output.wasm
```

Use a parser rather than byte offsets for anything beyond checking magic bytes;
LEB encodings and section lengths make manual patching fragile.

## Gotchas

- WAT identifiers are not stable ABI names; exports/imports use quoted names.
- Function declarations and code bodies live in separate binary sections.
- Unknown custom sections should be preserved or deliberately stripped, not
  mistaken for malformed standard sections.
- A tool may print newer WAT syntax that an older assembler cannot consume.

