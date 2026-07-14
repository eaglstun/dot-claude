# `topic_id` — hierarchical semantic IDs via RQ-VAE

**BUILT** — `scripts/topics.py`. This was the design; everything below now runs, and the
numbers in "What actually happened" are measured, not predicted.

The point is making the **prefix of an ID mean something**, which `design.md` correctly
proves is impossible with the sign-based code. It is possible here because the hierarchy is
_trained in_ rather than hoped for.

Read `design.md` first. This document contradicts one of its conclusions on purpose, and
the contradiction is the whole point.

## The idea in one paragraph

Today's `semantic_id` is `sign(v - mean)`: 172 independent bits, no structure between them.
Flip one high bit and the document lands at the far end of the sort order while staying
semantically adjacent — which is exactly why prefix-bucketing is a trap. **RQ-VAE**
(residual-quantized autoencoder) instead learns a small **codebook** of representative
directions, assigns each document the nearest one, computes the **residual** (what the
codebook missed), and quantizes _that_ against a second codebook, and so on down the
levels. The result is a code like `Q m 4 X r 9` where `Q` is a coarse topic, `m` narrows
it, `4` narrows further. The prefix genuinely _is_ a bucket, because each level was trained
to only describe what the previous levels got wrong.

The term of art for the output is, pleasingly, **"semantic IDs"** — the name arrived here
independently. The canonical writeup is Google's TIGER paper (_Recommender Systems with
Generative Retrieval_, Rajput et al., NeurIPS 2023), which uses RQ-VAE to give every item
in a catalogue a short hierarchical code.

## Rule 0: this does not touch `semantic_id`

`topic_id` is a **new, additive field**. Nothing is re-minted. Nothing existing changes.

```yaml
semantic_id: "aVl1Ldfhjxkb3j_DMYco2ggaiZ1sYAAG" # 172-bit Hamming code — unchanged
related_ids: ["...", "..."] # unchanged
topic_id: "Qm4Xr9" # NEW: 6 levels, one char each
topic_path: "gpu-compute/apple-metal/shaders" # NEW: what the prefix MEANS
```

The two codes answer different questions and there is no reason to make them compete:

| code          | question it answers       | how you use it               |
| ------------- | ------------------------- | ---------------------------- |
| `semantic_id` | "what is near this?"      | XOR + popcount, then rescore |
| `topic_id`    | "what bucket is this in?" | string prefix match          |

Keeping both means the RQ-VAE can fail, be retrained, or be thrown away entirely without
endangering a single ID already committed. That is the only reason this is worth doing at
all — see "what would invalidate everything," below.

## The format: one character per level

```
        topic_id = "Qm4Xr9"
                    │││││└─ level 6: finest residual
                    ││││└── level 5
                    │││└─── level 4
                    ││└──── level 3
                    │└───── level 2: subtopic  (64 per topic)
                    └────── level 1: coarse topic (64 buckets)
```

**6 levels × 6 bits = 36 bits = exactly 6 base64url characters, one char per level.** This
is the detail that makes the whole thing pleasant to live with: a codebook of K=64 entries
is 6 bits is precisely one base64 character, so **string prefix = semantic prefix**, with
no bit-shifting anywhere. `topic_id LIKE 'Qm%'` is a real topic scan. `sort by topic_id`
genuinely sorts by meaning. Grep works. Your eyes work.

At 283 documents a 64-way split at level 1 is far too aggressive (≈4 docs per bucket, and
most buckets empty). **Start at K=16 (4 bits) × L=4** while the corpus is small and the
codebooks are underfed, and grow to K=64 × L=6 if the corpus ever reaches five figures. The
one-char-per-level property survives if you keep K a power of 2 ≤ 64 and pad — but honestly,
below K=64 just accept that the character has unused range and keep the code readable.

Collisions are real and expected: two documents can quantize to the same code at every
level. TIGER appends a disambiguating token. **We already have one** — the existing 4-bit
tiebreak hash, same trick, already justified in `design.md`. Reuse it.

## Architecture

```
  doc text
     │  nomic-embed-text (FROZEN — the same model that mints semantic_id)
     ▼
  768 floats ─────────────────────────────────────────────┐
     │                                                    │
     │  encoder MLP  768 → 512 → 256 → d  (d ≈ 32)        │ reconstruction
     ▼                                                    │ target
    z (d floats)                                          │
     │                                                    │
     ├─ level 1: nearest of K codebook vectors → c₁       │
     │           r₁ = z  − e(c₁)                          │
     ├─ level 2: nearest of K → c₂                        │
     │           r₂ = r₁ − e(c₂)                          │
     ├─ level 3 …                                         │
     ├─ level L                                           │
     ▼                                                    │
    ẑ = Σ e(cᵢ)                                           │
     │  decoder MLP  d → 256 → 512 → 768                  │
     ▼                                                    │
  768 floats  ◄───────────────── reconstruction loss ─────┘

  topic_id = base64(c₁) ‖ base64(c₂) ‖ … ‖ base64(c_L)
```

The embedding model stays **frozen and off the training path**. We are not fine-tuning
nomic; we are learning a quantizer _on top of_ it. That keeps this cheap, keeps it
compatible with the existing `semantic_id` pipeline (same vectors, already cached in
`data/<context>.vectors.json`), and means a bad training run costs nothing but time.

### Losses

```
L = ‖x − x̂‖²                                    reconstruction (the real objective)
  + β · Σᵢ ‖ rᵢ₋₁ − sg[e(cᵢ)] ‖²                commitment  (encoder → codebook)
  + γ · Σᵢ ‖ sg[rᵢ₋₁] − e(cᵢ) ‖²                codebook    (codebook → encoder)
  + δ · entropy/balance penalty                  KEEP THE BUCKETS ALIVE
```

`sg[·]` is stop-gradient. The commitment/codebook split is the standard VQ-VAE formulation;
the gradient reaches the encoder through a straight-through estimator, because
nearest-neighbour lookup has no gradient (the same problem `sign()` has, and the same fix).

**The balance penalty is the one to actually care about**, and you already know why. Your
`stats` command measures **dead bits** and **skew from 50/50** — a bit identical across the
whole corpus carries zero information. The RQ-VAE equivalent is a **dead code**: a codebook
entry no document ever selects. It is the same pathology, and here it has a name and a
failure mode.

### Codebook collapse is THE failure mode

Untreated, RQ-VAE reliably collapses: a handful of codes win everything, the rest die, and
your "64-way topic split" is really a 5-way split with 59 corpses. Your `stats` output would
show it instantly — it is dead bits wearing a different hat. Mitigations, all standard, all
worth doing from day one rather than after you're confused:

- **k-means init.** Initialize each codebook from k-means over the actual residuals at that
  level. Never random-init. This alone fixes most of it.
- **EMA codebook updates** rather than gradient updates on the codebook (Sonnet/VQ-VAE-2
  style). More stable, less fiddly.
- **Dead-code restart.** Every N steps, find codes with ~zero usage and re-seed them onto
  high-residual training examples. This is the direct analogue of refusing to accept a dead
  bit.
- **Low codebook dimension.** Quantize in a small `d` (32ish), not in 768. Counterintuitive
  and load-bearing — high-dimensional codebooks collapse much more eagerly.

## The data problem, and why it is not fatal

283 documents cannot train a codebook. This is the identical objection that kills ITQ in
`design.md` ("with 84 pages, asking for 172 components means most are fitting noise"), and
it is just as true here.

**But RQ-VAE is unsupervised.** It is an autoencoder over embedding vectors. It needs no
labels, no pairs, no queries — only _vectors_, and it does not care whose vectors they are.

So:

1. Embed a **large external corpus** in the same broad domain (technical documentation,
   software prose) with the same frozen `nomic-embed-text`. Target 10⁵–10⁶ vectors. Sources
   worth considering: public docs corpora, your own `~/Documents/dev` repos' markdown, a
   HuggingFace technical-text dataset. It does not need to be _your_ documents. It needs to
   describe the same _region of the space_ your documents live in.
2. Train the RQ-VAE on those vectors. Reconstruction quality on held-out vectors is the
   metric; dead-code count is the health check.
3. **Freeze the codebooks** and ship them, exactly as the mean is frozen and shipped.
4. Apply the frozen quantizer to your 283 documents to get their `topic_id`s.

This decouples "how much data do I need to train" (a lot) from "how many documents do I
have" (283), and it is the move that makes the whole thing tractable. It also means the
codebooks, like the mean, become a **permanent frozen artifact** — see below.

Embedding ~500k chunks with nomic on the Mac is an overnight job, not a project. Training
the RQ-VAE itself is small — a few MLPs and some codebooks, minutes to an hour on the GPU,
and genuinely CPU-feasible if you're patient.

## The payoff: the prefix means something, in words

This is the part worth building, and it falls out almost for free.

Once documents are bucketed, take every document in bucket `Q`, hand their titles and
summaries to a local model, and ask it to **name the cluster**. Then do it for `Qm`, `Qm4`,
and so on down the tree.

```
Q     → "gpu-compute"           (41 docs)
  Qm  → "apple-metal"           (18 docs)
    Qm4 → "shaders-and-msl"     (7 docs)
    Qm9 → "memory-and-buffers"  (6 docs)
  Qk  → "cuda-and-nvidia"       (14 docs)
R     → "local-macos-data"      (9 docs)
  Rp  → "photos-and-media"      (3 docs)
```

That gives you `topic_path: "gpu-compute/apple-metal/shaders-and-msl"` in frontmatter, and
it gives you something the current system cannot produce at any price: **a taxonomy you
discovered rather than invented.** Note what else it is — a controlled vocabulary, derived
from the corpus's actual structure instead of hand-listed in `EXTRA_VOCAB`. The tags
question from `design.md` answers itself.

Naming clusters is exactly the job a local model is good at (a bounded, grounded,
summarize-these-20-titles task) and exactly the job it is bad at when asked to free-form
invent tags. Same model, right question this time.

## Integration

Additive, and gated behind config. Nothing changes for a context that doesn't ask.

```toml
[topics]
codebook   = "../data/topics-v1.codebook.json"   # FROZEN, like the mean
levels     = 4
codebook_k = 16
stamp      = true          # write topic_id + topic_path into frontmatter
label_model = "qwen35-cl46-abl-9b:latest"   # names the buckets
```

New commands, none of which disturb `mint`:

```bash
semantic_ids.py topics train  --vectors <big-corpus.json>   # once, then freeze
semantic_ids.py topics assign                               # stamp topic_id
semantic_ids.py topics label                                # name the buckets → topic_path
semantic_ids.py topics tree                                 # print the taxonomy
semantic_ids.py query --under Qm "how do I write a shader"  # prefix-scoped search
```

`--under` is the capability that justifies the whole exercise: a search restricted to a
subtree, resolved by string prefix, with no distance computation at all.

## Retrieval stays two-stage

Do not let a shiny hierarchy tempt you into throwing away the rescore. `design.md` is right:
a quantized code is a **filter, not a ranker**, and RQ-VAE does not change that — it changes
_what kind_ of filter. The pipeline becomes:

1. **Bucket** by `topic_id` prefix (or sweep by `semantic_id` Hamming — they compose).
2. **Rescore** the survivors with the full-precision float vectors.

Measured previously: shortlist + float rescore recovers **100%** of the exhaustive answer.
That number is why the binary code's ranking quality was never the bottleneck, and it is why
you should be honest that **this project buys navigability, not accuracy.** Retrieval
quality is already at ceiling. What you're buying is a browsable, nameable, prefix-scannable
structure — which is a real thing to want, and is not the same thing as better search.

## What would invalidate everything

The frozen-artifact list grows, and it grows in a way that should make you slightly nervous:

| artifact                     | size  | lose it and…                                     |
| ---------------------------- | ----- | ------------------------------------------------ |
| `<ctx>.mean.json` (existing) | 17 KB | every `semantic_id` is unreadable                |
| `topics-v1.codebook.json`    | ~MB   | every `topic_id` is unreadable                   |
| the encoder/decoder MLP      | ~MBs  | you cannot assign a `topic_id` to a new document |

Rule 1 now has a mortgage. Retraining the codebooks on a grown corpus **re-buckets every
document**, and unlike the mean — which is one 17 KB vector you can reason about — a
codebook is opaque. You will not be able to eyeball whether a retrain was safe.

Mitigations, in order of how much they matter:

- **Version the codebook in the filename** (`topics-v1`, `topics-v2`) and write the version
  into frontmatter (`topic_id: "v1:Qm4Xr9"`). Two IDs from different codebooks must never be
  silently comparable. This is the failure `design.md` warns about, and it is _more_ likely
  here because retraining will feel routine.
- **Train on the big external corpus, not on your 283 docs.** A codebook trained on 500k
  vectors doesn't need retraining when you add a skill. That is the whole reason for the
  external-corpus move — stability, not just data volume.
- **Keep `semantic_id` as the source of truth.** If the topic tree ever looks wrong, you can
  delete the entire `[topics]` apparatus and lose nothing but the taxonomy. That escape
  hatch is worth preserving deliberately.

## Honest scope

- **The weekend part:** train the RQ-VAE, assign codes, label the buckets, print the tree.
  Genuinely fun, genuinely tractable, real payoff you can look at.
- **The overnight part:** embedding a large external corpus. Boring, unattended.
- **The part that will actually eat your time:** codebook collapse. Budget for it. Expect
  the first three runs to produce a 64-way split that is really a 5-way split. `stats`-style
  dead-code diagnostics from the first commit, not after you're confused.
- **The part to not kid yourself about:** this does not make search better. Search is
  already at ceiling. It makes the corpus _navigable_, which is a different and more
  interesting thing to be able to say.


## What actually happened

Built and trained on `claude-home` (283 docs). The corpus is far too small to train a
codebook directly, so `train` **chunks the corpus** — every document's prose in 120-word
windows at 50% overlap — and trains on those. RQ-VAE is unsupervised, so it needs vectors,
not labels, and a chunk vector lives in the same region of the space as a document vector.
That turned 283 documents into ~4,800 training vectors.

**Collapse never happened.** 16/16 codes live at every level, from step one. k-means init +
EMA updates + dead-code restart, all in from the first commit rather than bolted on after
confusion. The measure that predicted trouble is the one that reported none.

**The real bug was a train/apply distribution mismatch, and it was invisible until labelled.**
v1 trained on chunks where doc vectors were only ~8% of the set. The codebook learned the
geometry of *paragraphs* and was then asked to bucket *abstracts* (`"Title. Summary."`).
Nothing in the loss curve or the dead-code counter showed it. It only became visible when a
local model named the buckets and two of them came back with the same name:

|                        | v1 (chunks only)                      | v2 (`doc_weight = 6`)          |
| ---------------------- | ------------------------------------- | ------------------------------ |
| `ct2-internals` docs   | **split across 2 level-1 buckets**    | **one bucket, 50 docs, 100%**  |
| largest incoherent bucket | 39 docs, named "tech-infrastructure" | none                        |
| duplicate level-1 names | yes (`F` and `K` both `ct2-internals`) | none                          |

Oversampling the doc vectors fixed it. This is worth remembering: **the health metrics said
the model was fine, and the model was fine — the DATA was pointed at the wrong target.** The
taxonomy itself was the diagnostic.

**Bucket quality after v2**, by how much of a bucket comes from one source directory:

    B  50 docs  ct2-internals              100%
    M  17 docs  msl-metal-shaders          100%
    J  28 docs  llm-concepts (glossary)     92%
    F  20 docs  calendar/email/imessage/hugo/digitalocean/guitar

`F` scores near-zero on that purity metric and is nonetheless **correct** — it clusters the
personal-tooling skills, which each live in their own directory and so can never share one.
The metric was wrong, not the bucket. Its *label* is genuinely bad, though
("semantic-search-tools" for a bin of calendar and guitar tooling), which is a fair summary
of where the weakness now lives: **the clustering is better than the naming.**

## Still open

- **K=64 needs the external corpus.** K=16 is what ~4,800 chunk vectors honestly support.
  The one-char-per-level property is already there and does not change.
- **Labels are the weak link, not the buckets.** Showing the model 25 titles and asking for
  one slug is thin. Showing it the titles *plus* what distinguishes this bucket from its
  siblings would be better.
- **Level-1 has ~16-way fan-out on 283 docs**, so levels 3–4 are mostly one document each
  and `topic_path` rarely goes deeper than two names. That is a corpus-size fact, not a bug.


## Labelling: contrastive prompting, then a measurement that overrules it

The first labeller showed the model one bucket at a time and asked what its documents had
in common. It named `{guitar, stonks, switchboard, want-me-to}` **"audio-tools"** — having
pattern-matched on one member and generalized. Asked what a set of things has in common, in
isolation, a model will ALWAYS find something.

**Fix 1 — contrastive prompting.** Show every sibling bucket in one call, require the names
to distinguish the buckets *from each other*, and enforce distinctness in code rather than
trusting the instruction. This worked: the seven CTranslate2 buckets that were all called
"ct2-internals" became `cpu-compute` / `core-ops` / `decoding-loop` / `python-bindings` /
`audio-encoder` / `model-format` / `device-management`. Zero duplicate names now exist
anywhere in the 86-bucket taxonomy.

**Fix 2 — stop asking the model to be honest, and measure it.** The prompt explicitly
licensed `mixed` as an answer for an incoherent bucket. Across 86 buckets the model used it
**zero times**. That is not a prompt bug you can fix with a firmer instruction; it is what
the machine is.

So compute it instead: mean pairwise cosine within a bucket, against the corpus baseline. A
real cluster is *tight*. Ranked by that number, the bottom of the list was exactly the
buckets flagged by eye — with no access to the names:

    corpus baseline                     0.637
    0.658  FC  calendar/digitalocean/email/network   → "calendar-sync"   ← confabulated
    0.661  FH  guitar/stonks/switchboard/want-me-to  → "audio-tools"     ← confabulated
    ...
    0.889  LE  metal-renderer + its references
    0.899  GO  int8 GEMM kernels

### The negative result, which matters more than the fix

**Cohesion measures tightness, and tightness is not coherence.**

The 26-term AI glossary bucket scores **0.625 — below the 0.637 baseline.** Its documents
are *less* similar to each other than two random documents are. And that is CORRECT: a
glossary deliberately spans a whole field (GAN, LoRA, temperature, alignment). It is a real
category that is genuinely not tight. Bucket F (calendar, guitar, stonks, hugo) also sits
below baseline, and is genuine junk.

**The measure cannot tell them apart.** Both are broad; one is real.

So the override is scoped to where it is actually reliable — buckets under ~15 documents,
where a low score really does mean grab-bag. On big buckets the number is printed as a
warning and the name stands. Tuning the threshold until it agreed with my prior would have
been the easy move and a dishonest one: it would have produced a taxonomy that looked right
and a metric that had stopped measuring anything.

Result: 5 of 86 buckets are now honestly `mixed`, including both confabulations above, and
the glossary keeps its name.
