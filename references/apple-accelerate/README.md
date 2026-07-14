---
topic_id: "v2:NINA"
topic_path: "apple-accelerate/sparse-solvers"
semantic_id: "9-_ohzE9PdqiUeOKQqwBOA5m3ldc4AAM"
related_ids:
  - "8m1kxju-EV6Cw2MfCrwBpAxTz79UwAAC"
  - "_-bsBuV9l9rySMOYA7aN4ChjXm7U8AAI"
---
# Apple Accelerate references

Condensed, source-cited notes from Apple's developer documentation for the **Accelerate**
framework — the CPU vectorized-math umbrella (BLAS/LAPACK, vDSP, vForce, simd, BNNS, Sparse
Solvers, vImage, Quadrature). Every file cites its Apple source URL(s) at the top and ends
with a `### Gotchas` section of the sharp edges memory gets wrong.

The **annotated index** (a one/two-line pointer per file) lives in the skill:
`skills/apple-accelerate/SKILL.md`, which also carries the "how to add a topic" recipe.

This is a **standalone framework shelf**, not tied to any one repo — the twin of the `rust`
and `swift` shelves. Repo conventions override anything here.

Siblings:

- **`apple-silicon`** (`references/apple-silicon/`) — the **GPU** counterpart (Metal / MPS).
  Accelerate is CPU; when data lives on the GPU, cross over there.
- **`swift`** (`references/swift/`) — the language shelf; the Swift-overlay pointer rules
  here assume its `withUnsafe*` / interop material.

## Conventions

Relative paths in `SKILL.md` are written from the skill dir (`skills/apple-accelerate/`);
from there this shelf is `../../references/apple-accelerate/`.

- Each reference cites its Apple **source URL** at the top and ends with `### Gotchas`.
- Prefer un-versioned `developer.apple.com/documentation/accelerate/...` URLs (they don't
  rot with OS releases).
- **Re-verifying a page:** the human doc pages are JS SPAs that return only a title to
  scrapers. Fetch the DocC JSON instead:
  `https://developer.apple.com/tutorials/data/documentation/accelerate/<path>.json`
  (e.g. `.../accelerate/vdsp.json`, `.../accelerate/bnns.json`).
- **Crosslinks** within the shelf use `[[file]]` in a `### See also` footer, each with a
  reason. Sibling-shelf links can use `[[shelf:file]]`.
- No `audit-citations.sh` here (unlike `apple-silicon`): these pages cite **doc URLs and
  API symbols**, not repo `file:line`, so there's nothing local to drift. Re-fetch the DocC
  JSON to check an API claim.

## TODO — topics worth mining on demand

Pull these into `*.md` when a task needs them; don't pre-build speculatively:

- **vImage geometry deep-dive** — affine/perspective warp math, the resampling kernels.
- **Sparse iterative solvers** — preconditioner choice (diagonal vs ILU), CG vs GMRES vs LSMR.
- **BNNSGraph end-to-end** — compiling a Core ML package into a `BNNSGraph.Context` with
  bound tensors (once a task actually exercises it).
- **DFT (non-power-of-two)** — `vDSP.DiscreteFourierTransform` setup/reuse, when it beats FFT.
