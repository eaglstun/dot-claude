---
topic_id: "v2:NOGB"
topic_path: "apple-accelerate/silicon-arch"
semantic_id: "3HD6Cu8-sN6kzLF5Xk5DFiBl146dsAAI"
related_ids:
  - "9HHwmh88uNwk4rH9Wk5DNmZhlTIbsAAK"
  - "3P98iM8kgN72r6S4Xs_jE2J1XwQb4AAL"
---
# Apple Silicon (Metal) GPU references

Condensed, source-cited notes from Apple's developer documentation and the MSL spec. The **API
bodies are repo-agnostic** — usable from any Metal GPU-compute codebase (PyTorch MPS kernels in
`aten/src/ATen/native/mps/`, the CTranslate2 Metal backend, standalone Metal).

Every file cites its Apple source URL at the top and ends with a `### Worked example: <repo>
<backend>` section grounding the API in real code. Those examples currently come from the
**CTranslate2 Metal backend** (`src/metal/`, `-DWITH_METAL=ON`), which is where this shelf was
mined. **They are illustrations, not instructions** — if you are not in CT2, read them as a case
study and do not map a `src/metal/` path onto a repo that has no such file.

`sources/` holds the vendored `Metal-Shading-Language-Specification.pdf` the MSL-kernel notes are
mined from.

These were moved here from the `apple-silicon` skill's local `references/`. The **annotated index**
(a one-line pointer per file) lives in that skill: `skills/apple-silicon/SKILL.md`, which also
carries the "how to add a topic" recipes and the MSL-section mining TODO.
`scripts/audit-citations.sh` there flags citation drift (its `REF_DIR` points here).

Siblings: the NVIDIA **CUDA** backend (the reference implementation this one mirrors) is the
`cuda-references` agent (`references/cuda/`); engine structure is `ct2-internals`
(`references/ct2-internals/`).

Cross-shelf: [[gpu-rosetta]] (repo root) maps every Metal concept here to its CUDA twin file.

## Conventions (moved from the skill's SKILL.md)

Relative paths below are written from the skill directory (`skills/apple-silicon/`); from
there this shelf is `../../references/apple-silicon/`.

- Each reference cites its Apple source URL at the top and ends with a
  `### Worked example: <repo> <backend>` section connecting the API to specific files in a **named**
  codebase. The shelf is machine-wide and read from many projects, so an unlabeled "the backend" is
  a trap — always name the repo, and append a new section rather than overwriting an existing one.
- Keep SKILL.md lean: one-line pointers only. Detail lives in `../../references/apple-silicon/`.
- **Code citations here drift.** Run `bash scripts/audit-citations.sh` (`-q` for
  problems-only) to flag missing files / out-of-range lines / ambiguous basenames; it
  prints each cited line so you can eyeball content drift it can't auto-detect. Most refs
  here cite by symbol/filename (drift-proof) — but a "verified on DATE" stamp dies the
  moment the file changes, so re-run rather than trust it.
- **Crosslinks to sibling shelves:** link as `[[shelf:file]]` (e.g. `[[cuda:cublas-gemm]]`)
  in a `### See also` footer, every link with a reason ("CUDA twin of…"). The CUDA↔Metal
  concept map + full convention spec is `~/.claude/references/gpu-rosetta.md`; check it
  before adding a GPU topic. MSL `[[attribute]]` syntax must stay inside code spans so it
  doesn't parse as a link. `bash ~/.claude/references/audit-crosslinks.sh` verifies.
- To add a topic from Apple's **DocC docs** (Metal framework API — `MTLDevice`,
  `MPSMatrixMultiplication`, etc.): fetch via the DocC JSON endpoint
  (`https://developer.apple.com/tutorials/data/documentation/<path>.json` — the human
  doc pages are JS SPAs that return only a title to scrapers), write a new
  `../../references/apple-silicon/<topic>.md` with the source URL + a CT2-relevance section, and add a
  pointer above.
- To add a topic from the **MSL standard library** (kernel-side functions / language —
  these are NOT on any DocC page): extract from the vendored spec PDF at
  `../../references/apple-silicon/sources/Metal-Shading-Language-Specification.pdf` (WebFetch rejects it — >10MB; needs
  `poppler`). Recipe:
  ```bash
  pdftotext -layout ../../references/apple-silicon/sources/Metal-Shading-Language-Specification.pdf /tmp/msl.txt
  grep -nE "^\s*6\.[0-9]" /tmp/msl.txt   # find the section's TOC entry + page
  sed -n 'START,ENDp' /tmp/msl.txt        # pull the section's line range
  ```

## TODO: more MSL references worth mining from the spec PDF

Carve these into `../../references/apple-silicon/*.md` when a task needs them (CT2-relevance, in priority order).
Don't pre-build speculatively — pull on demand, same discipline as the rest of the backend.

- ~~**§6.8 SIMD-Group Matrix Functions**~~ — DONE: see `../../references/apple-silicon/simdgroup-matrix-functions.md`
  (and the proven no-int8 fact that decided the int8 GEMM design).
- ~~**§6.16 Atomic Functions**~~ — DONE: see `../../references/apple-silicon/atomic-functions.md`.
- ~~**§6.6 Math Functions**~~ — DONE: see `../../references/apple-silicon/math-functions-and-numeric-parity.md`
  (math builtins, no-`erf`, fast-vs-precise ULP tables, the fast-math parity trap).
- ~~**§6.10.1 / §4.4.1** Threadgroup & SIMD-group **synchronization**~~ — DONE: see
  `../../references/apple-silicon/threadgroup-and-simdgroup-synchronization.md`.
- ~~**§6.3 Common Functions**~~ — DONE: see `../../references/apple-silicon/common-functions.md` (with §6.5
  relational/select in `../../references/apple-silicon/relational-and-select-functions.md`).
- NOT worth mining for CT2: textures (§6.13), imageblocks (§6.14), graphics/fragment
  (§6.11), geometric (§6.9) — no render passes in this backend.
