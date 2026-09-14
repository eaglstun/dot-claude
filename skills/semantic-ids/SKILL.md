---
name: semantic-ids
description: 'Semantic IDs — a 192-bit base64url string whose bits ARE the meaning of a document, so "what''s related to this" is an XOR and a popcount with no vector database. One engine, many corpora: ~/.agents (every skill, agent, and reference file) is one context; any project can define its own. Use when routing a request to the right skill/agent/reference by meaning rather than by grepping descriptions, when finding what''s semantically near a file, when adding semantic IDs to a new corpus or project, when a `semantic_id` looks wrong or two obviously-related documents score as unrelated, or when anything proposes changing the encoder or bit layout. Read this BEFORE editing a semantic_id by hand — several innocent-looking edits silently corrupt distances with no error.'
metadata:
  version: 2.0.0
  public: 'true'
  semantic_id: aVl1Ldfhjxkb3j_DMYco2ggaiZ1sYAAG
  related_ids: '["oaxHDAXLjplKZNXHI9OtV0paiTVlIAAF","KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"]'
  topic_id: v2:FJHK
  topic_path: site-tools/vector-search
---

# Semantic IDs

A semantic ID is not a random identifier. **Its bits are the meaning of the document.**

It's a binary-quantized text embedding: two documents about the same thing get IDs that
are close in **Hamming distance** (the count of differing bits). So "find related" becomes
an XOR and a popcount over a compact versioned string — no vector database, no server, nothing
to deploy.

```
v2:<──────────────────── 192 semantic bits ─────────────────────>
    deterministic calibrated SimHash = exactly 32 base64url chars, no padding
```

## Using it

```bash
S=~/.agents/skills/semantic-ids/scripts/semantic_ids.py

python3 $S query "how do I transcribe a video with speaker labels"
python3 $S near  ~/.agents/skills/whisperx/SKILL.md
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
where the documents are, how to read a title and summary out of them, and whether to stamp
IDs back into frontmatter.

| context                     | corpus                                                       |
| --------------------------- | ------------------------------------------------------------ |
| `claude-home` (default)     | `~/.agents`; the legacy context name preserves data filenames |
| `.agents/semantic-ids.toml` | whatever a project defines, auto-discovered from cwd         |

Resolution: `--context <name-or-path>` wins; otherwise the engine walks up from the current
directory looking for `.agents/semantic-ids.toml`, then the legacy `.claude/` location;
otherwise it falls back to `claude-home`.

The v2 encoder is stateless across corpora. Its SHA-256 projection seed and 65 broad
calibration sentences live in the script, and their origin is regenerated with the
configured embedding model. There is no corpus-derived mean to preserve. IDs remain tied
to the embedding model and encoder version, which are recorded in the index.

To add semantic IDs to a project, see **`references/contexts.md`**. It's one TOML file.

## Everything in `~/.agents` is stamped

Skills and agents get `semantic_id` written into their existing YAML frontmatter.
Reference files have no frontmatter, so they get a `---` block **prepended**. That's a real
mutation of a file that had none, and it's the right call here: `references/` holds
hand-written, source-cited condensed notes, not upstream text. The ID travelling _in_ the
file means it survives a lost index and `grep semantic_id` finds it.

**The one place not to stamp is a verbatim mirror.** `skills/openclaw-api/references/docs/`
mirrors upstream pages byte-for-byte so they diff clean against the source; prepending
frontmatter would destroy the only property that makes a mirror worth having. That tree
isn't in this context. If you add a corpus like it, set `stamp = false` and let the sidecar
index carry the IDs — `query` and `near` read it either way.

## `related_ids` — the two nearest neighbours, in the file

Every stamped file also carries the IDs of its two closest documents:

```yaml
semantic_id: "v2:0H0AFzKRsgoDcilfc5IC1eIVAcMTT4FD"
related_ids:
  - "v2:1H0AFzKRsgoDcilfc5IC1eIVAcMTT4FD"
  - "v2:2H0AFzKRsgoDcilfc5IC1eIVAcMTT4FD"
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

An inline `related_ids: ["...", "..."]` of two versioned IDs is over 90 characters — past a
markdown formatter's 80-column print width. Prettier wraps it onto a continuation line,
and a line-based frontmatter editor then replaces the key while orphaning the fragment
below it. That produces invalid YAML, which means the skill's `description` stops parsing,
which means **the skill silently stops loading**. It happened. The block form is what the
formatter would have written anyway, so it survives being formatted. Never emit a
frontmatter value long enough to wrap.

## The three rules

Break any of these and the IDs corrupt **silently** — no error, no warning, just quietly
wrong distances that still look like plausible numbers.

**1. Encoder versions never mix.**
v1 used 172 mean-centered bits plus a 20-bit date/hash tail. v2 uses all 192 bits for a
calibrated SimHash and carries `v2:` in the value. The helper refuses cross-version
comparisons. Changing the projection seed, calibration sentences, embedding model, or
embedded text requires a new version and a deliberate full re-mint.

**2. `-` is a character in the ID, not a separator.**
The ID is base64url, whose alphabet is `A–Z a–z 0–9 - _`. It looks enough like a UUID to
invite a reflexive `.replace("-", "")`. Do that and you delete real bits out of the middle
of the ID. Use `decode64()`.

**3. Tags, where a context enables them, come from a controlled vocabulary. Never free-form.**
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
  dead bits            0 / 192
  mean pair distance    ~96 bits  (chance = 96)
```

A **dead bit** is identical on every document and therefore carries exactly zero
information for that corpus. Two unrelated documents should differ by about **half** the
semantic bits — a coin flip. The fixed 65-domain calibration suite measures 97 bits on
average against a chance value of 96, with no dead bits.

If related lists look like noise, check `stats` before you touch anything else.

## Deeper background

- **`references/contexts.md`** — the context TOML format, field by field, and how to add
  semantic IDs to a project.
- **`references/design.md`** — why binary quantization works, why raw zero is a bad origin,
  why the prefix-as-semantic-bucket idea is a trap, the v1 encoder comparison, the v2
  stateless design, and the two-stage retrieval architecture. Read it before changing the
  bit layout, encoder, calibration suite, or embedding model.
- **`references/rqvae.md`** — the built topic taxonomy. It makes an ID's **prefix mean
  something** (`topic_id: "Qm4Xr9"` → `gpu-compute/apple-metal/shaders`) by training a
  residual-quantized autoencoder, which is the one thing `design.md` proves the current
  sign-based code can never do. Additive: it does not touch `semantic_id`.

Do not reach for a vector database. At this corpus size that is a punchline.
