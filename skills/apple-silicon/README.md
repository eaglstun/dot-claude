# apple-silicon skill

Metal / Apple Silicon GPU documentation reference for the CTranslate2 Metal backend.

Entry point is [SKILL.md](SKILL.md); the actual docs live in the shared
[`references/apple-silicon/`](../../references/apple-silicon/) (moved out of this skill dir
into the repo-wide reference library — the MSL spec PDF moved with them to
`../../references/apple-silicon/sources/`). Each reference is condensed from Apple's developer
documentation (source URL cited at the top) and ends with a section tying the API to specific
files in `src/metal/`.

`scripts/` holds `audit-citations.sh` (flags missing files / out-of-range lines / ambiguous
basenames in the references' citations).
