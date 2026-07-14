---
name: semantic-ids
version: 1.0.0
description: >-
  Semantic IDs — a 192-bit base64url string whose bits ARE the meaning of a document, so
  "what's related to this" is an XOR and a popcount with no vector database. One engine,
  many corpora: ~/.claude (every skill, agent, and reference file) is one context; any
  project can define its own. Use when routing a request to the right skill/agent/reference
  by meaning rather than by grepping descriptions, when finding what's semantically near a
  file, when adding semantic IDs to a new corpus or project, when a `semantic_id` looks
  wrong or two obviously-related documents score as unrelated, or when anything proposes
  recomputing a frozen mean or changing the bit layout. Read this BEFORE editing a
  semantic_id or a frozen mean by hand — several innocent-looking edits silently corrupt
  every ID in the corpus, with no error.
public: true
semantic_id: "aVl1Ldfhjxkb3j_DMYco2ggaiZ1sYAAG"
related_ids:
  - "oaxHDAXLjplKZNXHI9OtV0paiTVlIAAF"
  - "KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"
topic_id: "v2:FJHK"
topic_path: "site-tools/vector-search"
---

# Semantic IDs

A semantic ID is not a random identifier. **Its bits are the meaning of the document.**

It's a binary-quantized text embedding: two documents about the same thing get IDs that
are close in **Hamming distance** (the count of differing bits). So "find related" becomes
an XOR and a popcount over a 32-character string — no vector database, no server, nothing
to deploy.

```
┌──────────────── 172 bits semantic ───────────────┬── 16b day ──┬─ 4b hash ─┐
│  sign(embedding[i] - frozenMean[i]),  i = 0..171 │ since epoch │ tiebreak  │
└──────────────────────────────────────────────────┴─────────────┴───────────┘
 192 bits total = 24 bytes = exactly 32 base64url chars, no padding
```

## Using it

```bash
S=~/.claude/skills/semantic-ids/scripts/semantic_ids.py

python3 $S query "how do I transcribe a video with speaker labels"
python3 $S near  ~/.claude/skills/whisperx/SKILL.md
python3 $S mint                     # stamp anything new; idempotent
python3 $S stats                    # bit health — dead bits, skew, distance spread
```

`query` is the one you'll reach for. It answers **"which skill, agent, or reference covers
this?"** by meaning rather than by grepping descriptions for keywords:

```
$ python3 $S query "the GPU ran out of memory during a matmul"

  0.710   65b  [references] apple-silicon: MPSMatrixMultiplication
  0.693   73b  [references] apple-silicon: Metal 4 tensors & Metal Performance Primitives
  0.689   71b  [skills]     apple-silicon
```

Needs Ollama with `nomic-embed-text`. Standard library only — no pip, no venv.

## Contexts

The engine knows nothing about any particular corpus. A **context** is a TOML file saying
where the documents are, how to read a title and summary out of them, whether to stamp IDs
back into frontmatter, and where that corpus's **frozen mean** lives.

| context                     | corpus                                                                          |
| --------------------------- | ------------------------------------------------------------------------------- |
| `claude-home` (default)     | `~/.claude` — 283 docs: 41 skills, 10 agents, 37 glossary terms, 195 references |
| `.claude/semantic-ids.toml` | whatever a project defines, auto-discovered from cwd                            |

Resolution: `--context <name-or-path>` wins; otherwise the engine walks up from the current
directory looking for `.claude/semantic-ids.toml`; otherwise it falls back to `claude-home`.

**Each context has its own frozen mean, and means are not shareable.** The mean is the
origin every ID in that corpus is measured against. Two corpora with different origins
produce IDs that are not comparable to each other, and nothing will tell you — the
distances will still be numbers.

To add semantic IDs to a project, see **`references/contexts.md`**. It's one TOML file.

## Everything in `~/.claude` is stamped

Skills and agents get `semantic_id` written into their existing YAML frontmatter.
Reference files have no frontmatter, so they get a `---` block **prepended**. That's a real
mutation of a file that had none, and it's the right call here: `references/` holds
hand-written, source-cited condensed notes, not upstream text. The ID travelling _in_ the
file means it survives a lost index and `grep semantic_id` finds it.

**The one place not to stamp is a verbatim mirror.** `skills/your-api-skill/references/docs/`
mirrors upstream pages byte-for-byte so they diff clean against the source; prepending
frontmatter would destroy the only property that makes a mirror worth having. That tree
isn't in this context. If you add a corpus like it, set `stamp = false` and let the sidecar
index carry the IDs — `query` and `near` read it either way.

## `related_ids` — the two nearest neighbours, in the file

Every stamped file also carries the IDs of its two closest documents:

```yaml
semantic_id: "aVl1Ldfhjxkb3j_DMYco2ggaiZ1sYAAG"
related_ids:
  ["oaxHDAXLjplKZNXHI9OtV0paiTVlIAAF", "KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"]
```

**IDs, not paths** — a path breaks the day you rename a folder; an ID doesn't. Resolve one
back to a file with `near <path>`, which prints the neighbours with their titles, or grep
the ID across the corpus.

**Unlike `semantic_id`, this list is derived and is rewritten on every run — and must be.**
A new document is a new neighbour for one stamped a year ago. Rewriting a derived list
cannot corrupt an ID, so it's the one thing here that's allowed to churn. Set
`related_stamp = 0` in a context to skip it.

It obeys `related_max_distance`, so a document with nothing inside the cutoff gets an
explicit `related_ids: []` rather than a nearest-of-the-noise. In `claude-home` that's
`switchboard` — a master index of everything is specifically about nothing, so it sits
alone in the middle of the space, which is exactly right.

**Lists are written as a YAML block sequence, and that is load-bearing:**

```yaml
related_ids:
  - "kzQArUM6XzcK1BKXaiid5m-aYMYSEAAO"
  - "aPwFGVu6RbetOrhRNi-Xh--qZJykcAAJ"
```

An inline `related_ids: ["...", "..."]` of two 32-char IDs is 85 characters — past a
markdown formatter's 80-column print width. Prettier wraps it onto a continuation line,
and a line-based frontmatter editor then replaces the key while orphaning the fragment
below it. That produces invalid YAML, which means the skill's `description` stops parsing,
which means **the skill silently stops loading**. It happened. The block form is what the
formatter would have written anyway, so it survives being formatted. Never emit a
frontmatter value long enough to wrap.

## The four rules

Break any of these and the IDs corrupt **silently** — no error, no warning, just quietly
wrong distances that still look like plausible numbers.

**1. The frozen mean is frozen. Never recompute it.**
`data/<context>.mean.json` holds the 768-float corpus mean, and binarization is
`sign(v - mean)`. That mean was computed once, from the corpus as it stood, and it is the
shared reference frame every ID is measured against. Recompute it on a grown corpus and
_every previously-issued ID becomes wrong_ — they were minted against a different origin.
The script only writes the file if it doesn't already exist. Do not delete it. Do not
"refresh" it. **It is the one artifact here that is genuinely irreplaceable**, which is why
it's the only one committed to git (the index and float vectors are regenerable in
seconds, and `.gitignore`d).

**2. `-` is a character in the ID, not a separator.**
The ID is base64url, whose alphabet is `A–Z a–z 0–9 - _`. It looks enough like a UUID to
invite a reflexive `.replace("-", "")`. Do that and you delete real bits out of the middle
of the ID. Use `decode64()`.

**3. Always compare through the mask.**
The bottom 20 bits are a date and a tiebreak hash. To Hamming distance they are pure
**noise** — two identical documents dated a year apart differ by ~10 tail bits for no
semantic reason. Use the `hamming()` helper, which masks them off. Comparing raw IDs is the
single most likely way to make this system look broken when it isn't.

**4. Tags, where a context enables them, come from a controlled vocabulary. Never free-form.**
Anything the model invents that isn't on the list is dropped on the floor. This is not
fussiness: free-form generation produced `aspartame-grade-ml`, `sepahora-bot`, and
`three-hours-150-dollars`, and bolted `attention-mechanism` onto essays about labour policy.
**Tags feed the embedding text**, so junk tags mean junk vectors — strictly worse than no
tags at all. (`claude-home` uses no tags: a skill's `description` is already the best
one-sentence statement of what it's for, which is the job a tag list would be doing worse.)

Also: never add a tag that would be true of every document. A tag that describes everything
discriminates nothing. It's the taxonomy version of a dead bit — address space you paid for
and can't use.

## What gets embedded

`title + summary` (+ tags, if the context has them). **Not the body.**

An embedding is a fixed-size container — 768 floats whether you hand it a sentence or an
entire manual. Feed it a whole document and you get the _centroid_ of everything in it: a
vector that is near everything and specifically about nothing. One embedding should hold
about one idea.

For skills and agents that's `name` + `description`. For a reference file with no
frontmatter it's `<parent dir>: <first H1>` + the first prose paragraph — the directory is
in there because a bare H1 like "Overview" doesn't discriminate across a dozen library
folders, but `cuda` vs `rust` genuinely does.

## Is it working?

`stats` is the health check. Two numbers decide it:

```
  dead bits            0 / 172   (must be 0)
  mean pair distance  86.2 bits  (chance = 86)
```

A **dead bit** is identical on every document and therefore carries exactly zero
information. Any dead bit at all means the mean doesn't fit the corpus. And two unrelated
documents should differ by about **half** the semantic bits — a coin flip. `claude-home`
lands at 86.2 against a chance value of 86, which is what a healthy corpus looks like.

If related lists look like noise, check `stats` before you touch anything else.

## Deeper background

- **`references/contexts.md`** — the context TOML format, field by field, and how to add
  semantic IDs to a project.
- **`references/design.md`** — why binary quantization works at all, why mean-centering is
  mandatory, why the prefix-as-semantic-bucket idea is a trap, the encoder comparison
  (truncate vs ITQ vs SimHash vs PCA) and why this uses the _simplest_ one, the two-stage
  retrieval architecture, and the measured recall numbers. Read it before changing the bit
  layout, the encoder, or the embedding model.
- **`references/rqvae.md`** — a SPEC, not built. How to make the ID's **prefix mean
  something** (`topic_id: "Qm4Xr9"` → `gpu-compute/apple-metal/shaders`) by training a
  residual-quantized autoencoder, which is the one thing `design.md` proves the current
  sign-based code can never do. Additive: it does not touch `semantic_id`.

Do not reach for a vector database. At this corpus size that is a punchline.
