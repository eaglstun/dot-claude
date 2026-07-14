# Contexts — adding semantic IDs to a corpus

A **context** is one TOML file. It says where the documents are, how to read a title and
summary out of them, whether to stamp IDs back into their frontmatter, and where that
corpus's frozen mean lives. The engine knows nothing else about your corpus.

## Where a context lives

| you want                  | put the TOML at                                                                |
| ------------------------- | ------------------------------------------------------------------------------ |
| a corpus inside a project | `<project>/.claude/semantic-ids.toml` — auto-discovered by walking up from cwd |
| another user-level corpus | `~/.claude/skills/semantic-ids/contexts/<name>.toml` — then `--context <name>` |
| a one-off                 | anywhere; `--context /path/to/it.toml`                                         |

Resolution order: explicit `--context` wins, then the nearest `.claude/semantic-ids.toml`
walking up from the working directory, then `claude-home`.

## The whole format

```toml
name = "my-project"          # names the data files: <name>.mean.json, .index.json, .vectors.json

embed_model = "nomic-embed-text"
ollama      = "http://127.0.0.1:11434"

data_dir = "./semantic"      # relative to THIS file. Holds the frozen mean + index.

date_field = "date"          # optional. A frontmatter field holding YYYY-MM-DD. Omit and
                             # every ID carries day 0 — stable, and honest about having no date.

related_count        = 6     # how many neighbours to record per document
related_max_distance = 68    # the cutoff. CALIBRATE IT — see below.

[[source]]
name         = "posts"
root         = "./content/blog"   # relative to this file, or absolute, or ~/…
glob         = "**/*.md"
exclude      = ["**/_index.md"]   # optional list of glob patterns
frontmatter  = "toml"             # "toml" (+++), "yaml" (---), or "none"
title_field   = "title"           # which frontmatter field is the title
summary_field = "summary"         # which is the one-sentence summary
stamp        = true               # write semantic_id back into the file's frontmatter?
```

Multiple `[[source]]` blocks share one context, one frozen mean, and one index — which is
the point. Documents are only comparable to each other if they were minted against the
same origin, so put everything you want to compare in **one** context.

### `frontmatter = "none"`

For files with no frontmatter (plain docs, mirrored upstream documentation). The engine
takes:

- **title** = `<parent directory>: <first H1>`, or the filename stem if there's no H1.
  The directory is in there because a bare H1 like "Overview" doesn't discriminate across
  a dozen folders, but `cuda` vs `rust` genuinely does.
- **summary** = the first real prose paragraph (skipping headings, lists, fences, tables,
  blockquotes).

A document with no summary at all is **skipped**, not minted. An ID computed from a
filename is a lie with 172 bits of false precision.

### `stamp`

`true` writes `semantic_id` into the file's frontmatter. `false` puts it in the sidecar
index only and never touches the file — which is what you want for anything that must stay
byte-identical to an upstream source, like a verbatim doc mirror.

If `stamp = true` on a source with `frontmatter = "none"`, the engine **prepends** a new
YAML block. That's a real mutation of a file that had none. It's allowed because you asked.

## Tags are opt-in, and off by default

```toml
[tags]
chat_model = "qwen35-cl46-abl-9b:latest"
count      = 6
vocab      = ["inference", "quantization", "fine-tuning", "rag", "…"]
```

Omit the `[tags]` block entirely and no tagging model is ever called — the embedding text
is just title + summary. **This is the right default.** Reach for tags only when your
titles and summaries are genuinely too thin to distinguish documents.

If you do enable them: `vocab` is a **controlled vocabulary** and it is not optional.
Anything the model invents that isn't on the list is dropped on the floor. Free-form
generation produced `aspartame-grade-ml`, `sepahora-bot`, and `three-hours-150-dollars`,
and bolted `attention-mechanism` onto essays about labour policy. Tags feed the embedding
text, so junk tags mean junk vectors — strictly worse than no tags at all.

And never put a tag in the vocabulary that would be true of every document (`writing`,
`ai`, `code`). A tag that describes everything discriminates nothing.

## Then

```bash
S=~/.claude/skills/semantic-ids/scripts/semantic_ids.py

python3 $S mint --dry-run    # ALWAYS first. Confirms the reader found your documents
                             # and read real titles and summaries out of them.
python3 $S mint              # computes and FREEZES the mean; mints; stamps; indexes
python3 $S stats             # bit health — read this before trusting anything
```

## Calibrating `related_max_distance`

Do not copy a number from another corpus. Mint, then run `stats`:

```
  dead bits            0 / 172   (must be 0)
  mean pair distance  86.2 bits  (chance = 86)
  5th percentile        68 bits  ← a sane related_max_distance
```

Two unrelated documents should differ by about **half** the semantic bits — a coin flip.
The 5th percentile of all pairwise distances is the honest cutoff: it means "closer than
~95% of random pairs." Past that you are ranking noise and calling the winner a
recommendation.

`related_max_distance` is a derived list, so changing it and re-running is **safe** — it
rewrites neighbour lists and cannot corrupt an ID.

## What is safe to change, and what is a one-way door

| change                                     | consequence                                                                                      |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| `related_count`, `related_max_distance`    | safe. Derived lists, rewritten every run.                                                        |
| adding documents, adding a `[[source]]`    | safe. New docs mint against the existing mean.                                                   |
| `stamp`                                    | safe. Changes where the ID is written, not what it is.                                           |
| **`embed_model`**                          | **re-mint everything.** The engine refuses to run against a mean trained with a different model. |
| **the vocab, or what text is embedded**    | **re-mint everything.** Different input, different vector.                                       |
| **`SEMANTIC_BITS` / `DAY_BITS` / `EPOCH`** | **re-mint everything.** Different bit layout.                                                    |
| **recomputing or deleting the mean**       | **every existing ID silently becomes wrong.** See rule 1.                                        |

There is no migration. IDs minted under different settings are not comparable, and nothing
will tell you — the distances will still be numbers.
