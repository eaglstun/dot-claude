#!/usr/bin/env python3
"""
topic_id — hierarchical semantic IDs via RQ-VAE. The prefix MEANS something.

Where `semantic_id` is 172 independent bits with no structure between them (flip a high bit
and a document flies to the far end of the sort order while staying semantically adjacent),
a topic_id is a chain of nested buckets:

        topic_id = "Gm4X"
                    ││││
                    │││└─ level 4: finest residual
                    ││└── level 3
                    │└─── level 2: subtopic
                    └───── level 1: coarse topic

Each level quantizes the RESIDUAL — what the levels above it failed to capture — so the
hierarchy is trained in rather than hoped for. One codebook entry = one base64 character, so
STRING prefix == SEMANTIC prefix. `topic_id LIKE 'Gm%'` is a real topic scan, sorting by
topic_id sorts by meaning, and grep works.

    topics.py train     # embed corpus chunks, train the RQ-VAE, FREEZE the codebook
    topics.py assign    # stamp topic_id into frontmatter
    topics.py label     # name every bucket with a local model → topic_path
    topics.py tree      # print the taxonomy

RULE 0: this NEVER touches semantic_id. topic_id is additive. If the taxonomy ever looks
wrong you can delete the whole [topics] apparatus and lose nothing but the taxonomy — that
escape hatch is deliberate, and it is the only reason this is safe to ship.

`train` needs torch. `assign`/`label`/`tree` need only numpy + the frozen codebook, so the
day-to-day path stays cheap. See references/rqvae.md for the design.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_ids import (  # noqa: E402
    ALPHABET,
    collect,
    data_file,
    doc_text,
    embed,
    load_context,
    post,
    quote,
    set_fields,
    yaml_list,
)

CHUNK_WORDS = 120
CHUNK_STRIDE = 60  # 50% overlap — more training vectors, and boundaries stop mattering


# ── the frozen artifact ───────────────────────────────────────────────────────


def codebook_path(cfg: dict) -> Path:
    t = cfg.get("topics", {})
    return cfg["_data"] / f"{cfg['_name']}.topics-{t.get('version', 'v1')}.json"


def load_codebook(cfg: dict) -> dict:
    p = codebook_path(cfg)
    if not p.exists():
        sys.exit(f"no codebook at {p} — run `topics.py train` first")
    m = json.loads(p.read_text())
    if m["embed_model"] != cfg["embed_model"]:
        sys.exit(f"codebook was trained on {m['embed_model']!r}, context uses "
                 f"{cfg['embed_model']!r} — the topic_ids would be meaningless")
    return m


# ── encode / decode a topic_id ────────────────────────────────────────────────


def encode_topic(codes: list[int], version: str) -> str:
    """
    One codebook entry → one base64url character. This is the property the whole design
    rests on: string prefix IS semantic prefix, with no bit-shifting anywhere.

    The version prefix is not decoration. Two topic_ids from different codebooks are not
    comparable and NOTHING else would tell you — the strings would still look like strings.
    Retraining a codebook will feel routine in a way that recomputing the frozen mean never
    did, which is exactly why the guard has to be inside the ID itself.
    """
    return f"{version}:" + "".join(ALPHABET[c] for c in codes)


def decode_topic(tid: str) -> tuple[str, list[int]]:
    version, _, code = tid.partition(":")
    return version, [ALPHABET.index(c) for c in code]


# ── the model, at inference: pure numpy, no torch ─────────────────────────────


def encode_vectors(model: dict, X: np.ndarray) -> list[list[int]]:
    """
    Run the frozen encoder, then quantize the residual at each level.

    This is deliberately numpy-only. Assigning a topic_id to a new document must not
    require a deep-learning stack — the same instinct that keeps the rest of the engine on
    the standard library.
    """
    h = X
    for W, b in zip(model["enc_w"], model["enc_b"]):
        h = h @ np.array(W, dtype=np.float32) + np.array(b, dtype=np.float32)
        h = np.maximum(h, 0) if W is not model["enc_w"][-1] else h  # ReLU except last

    codes: list[list[int]] = [[] for _ in range(len(h))]
    residual = h.copy()
    for level in model["codebooks"]:
        C = np.array(level, dtype=np.float32)                       # (K, d)
        d2 = ((residual[:, None, :] - C[None, :, :]) ** 2).sum(-1)  # (N, K)
        idx = d2.argmin(1)
        for i, c in enumerate(idx):
            codes[i].append(int(c))
        residual = residual - C[idx]
    return codes


# ── train ─────────────────────────────────────────────────────────────────────


def chunks_of(text: str) -> list[str]:
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    body = re.sub(r"```.*?```", "", body, flags=re.S)  # code fences are not prose
    words = body.split()
    out = []
    for i in range(0, max(1, len(words) - CHUNK_WORDS // 2), CHUNK_STRIDE):
        c = " ".join(words[i : i + CHUNK_WORDS])
        if len(c.split()) >= 30:
            out.append(c)
    return out


def cmd_train(cfg: dict, args) -> None:
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        sys.exit("`train` needs torch (assign/label/tree do not). pip install torch")

    tcfg = cfg.get("topics", {})
    L = tcfg.get("levels", 4)
    K = tcfg.get("codebook_k", 16)
    D = tcfg.get("latent_dim", 32)
    version = tcfg.get("version", "v1")

    out = codebook_path(cfg)
    if out.exists() and not args.force:
        sys.exit(f"{out} exists. A codebook is FROZEN — retraining re-buckets every "
                 f"document. Bump `version` in the context, or pass --force to overwrite "
                 f"and accept that every existing topic_id becomes wrong.")

    # ── training vectors ──────────────────────────────────────────────────────
    #
    # RQ-VAE is UNSUPERVISED — it is an autoencoder over vectors and does not care whose
    # vectors they are. That is what rescues it from the objection that kills ITQ in
    # design.md ("with 84 pages, asking for 172 components means most fit noise"): we do
    # not need 283 LABELLED documents, we need a lot of VECTORS from the same region of
    # the space. So we chunk the corpus and embed the chunks.
    #
    # This is still thin. A K=64 codebook wants an external corpus of 10^5+ vectors (see
    # references/rqvae.md). K=16 on a few thousand chunks is honest; K=64 on them would be
    # 80% dead codes wearing a hat.
    docs = collect(cfg)
    vecs_path = data_file(cfg, "topic-train-vectors")
    if vecs_path.exists() and not args.re_embed:
        X = np.array(json.loads(vecs_path.read_text()), dtype=np.float32)
        print(f"reusing {len(X):,} cached training vectors ({vecs_path.name})")
    else:
        # The codebook is TRAINED on chunks but APPLIED to doc vectors, and those are
        # different distributions — a chunk is a prose paragraph, a doc vector is
        # "Title. Summary." Left alone, doc vectors are ~8% of the training set, the
        # codebook learns the geometry of paragraphs, and it buckets abstracts badly:
        # measured on v1, that produced a 39-document junk drawer and split one topic
        # (ct2-internals) across two level-1 buckets.
        #
        # Oversampling the doc vectors fixes the mismatch. The chunks are still doing the
        # real work — they are what makes a codebook trainable on a 283-document corpus at
        # all — but they no longer get to define the space by themselves.
        w = cfg.get("topics", {}).get("doc_weight", 1)
        texts = []
        for d in docs:
            texts.extend([doc_text(cfg, d)] * w)  # the doc-level vector, oversampled
            texts.extend(chunks_of(d["body"]))    # plus its prose, in windows
        print(f"embedding {len(texts):,} chunks from {len(docs)} docs "
              f"with {cfg['embed_model']}...")
        X = np.array(embed(cfg, texts), dtype=np.float32)
        vecs_path.write_text(json.dumps(X.tolist()))

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    Xt = torch.tensor(X, device=dev)
    n, dim = Xt.shape
    print(f"\ntraining RQ-VAE on {n:,} × {dim} vectors  ({dev})")
    print(f"  {L} levels × {K} codes, latent dim {D} → {K**L:,} possible buckets")

    class Enc(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(dim, 512), nn.ReLU(),
                nn.Linear(512, 256), nn.ReLU(),
                nn.Linear(256, D),
            )

        def forward(self, x):
            return self.net(x)

    class Dec(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(D, 256), nn.ReLU(),
                nn.Linear(256, 512), nn.ReLU(),
                nn.Linear(512, dim),
            )

        def forward(self, z):
            return self.net(z)

    enc, dec = Enc().to(dev), Dec().to(dev)
    opt = torch.optim.Adam([*enc.parameters(), *dec.parameters()], lr=1e-3)

    # ── the codebooks, with every anti-collapse measure from the spec ─────────
    #
    # Untreated, RQ-VAE reliably collapses: a few codes win everything and the rest die,
    # so a "16-way split" is really a 4-way split with 12 corpses. This is the DEAD BIT
    # problem wearing a different hat — the same pathology `stats` already measures for
    # semantic_id — and it is the single thing most likely to eat a weekend.
    #
    #   k-means init      never random-init; seed from the actual residuals at that level
    #   EMA updates       codebooks move by exponential moving average, not by gradient
    #   dead-code restart re-seed unused codes onto the worst-reconstructed inputs
    #   low latent dim    quantize in D≈32, not 768 — high-dim codebooks collapse eagerly
    codebooks = [torch.zeros(K, D, device=dev) for _ in range(L)]
    ema_count = [torch.ones(K, device=dev) for _ in range(L)]
    ema_sum = [torch.zeros(K, D, device=dev) for _ in range(L)]
    initialized = [False] * L
    DECAY, BETA, DEAD = 0.99, 0.25, 1.0

    def kmeans(x: torch.Tensor, k: int, iters: int = 25) -> torch.Tensor:
        c = x[torch.randperm(len(x), device=dev)[:k]].clone()
        for _ in range(iters):
            d2 = torch.cdist(x, c) ** 2
            a = d2.argmin(1)
            for j in range(k):
                m = a == j
                if m.any():
                    c[j] = x[m].mean(0)
                else:  # a cluster died during init — restart it on the worst-fit point
                    c[j] = x[d2.min(1).values.argmax()]
        return c

    steps = args.steps
    batch = min(512, n)
    for step in range(1, steps + 1):
        idx = torch.randint(0, n, (batch,), device=dev)
        x = Xt[idx]
        z = enc(x)

        residual, quant, commit = z, torch.zeros_like(z), 0.0
        for lv in range(L):
            if not initialized[lv]:
                with torch.no_grad():
                    codebooks[lv] = kmeans(residual.detach(), K)
                    ema_sum[lv] = codebooks[lv].clone()
                initialized[lv] = True

            d2 = torch.cdist(residual, codebooks[lv]) ** 2
            a = d2.argmin(1)
            e = codebooks[lv][a]
            commit = commit + ((residual - e.detach()) ** 2).mean()

            if enc.training:
                with torch.no_grad():
                    onehot = torch.zeros(batch, K, device=dev)
                    onehot[torch.arange(batch, device=dev), a] = 1
                    ema_count[lv].mul_(DECAY).add_(onehot.sum(0), alpha=1 - DECAY)
                    ema_sum[lv].mul_(DECAY).add_(onehot.T @ residual.detach(), alpha=1 - DECAY)
                    codebooks[lv] = ema_sum[lv] / ema_count[lv].clamp(min=1e-5).unsqueeze(1)

                    dead = ema_count[lv] < DEAD
                    if dead.any() and step % 50 == 0:
                        # Re-seed dead codes onto the WORST-reconstructed inputs. A code no
                        # document ever selects is address space you paid for and cannot use.
                        worst = d2.min(1).values.argsort(descending=True)[: int(dead.sum())]
                        codebooks[lv][dead] = residual.detach()[worst]
                        ema_sum[lv][dead] = residual.detach()[worst]
                        ema_count[lv][dead] = 1.0

            quant = quant + e
            residual = residual - e

        # straight-through: forward uses the quantized code, backward pretends it didn't.
        # Nearest-neighbour lookup has no gradient — the same problem sign() has, same fix.
        zq = z + (quant - z).detach()
        recon = dec(zq)
        loss = ((recon - x) ** 2).mean() + BETA * commit

        opt.zero_grad()
        loss.backward()
        opt.step()

        if step % max(1, steps // 10) == 0 or step == 1:
            with torch.no_grad():
                alive = [int((c > DEAD).sum()) for c in ema_count]
            print(f"  step {step:>5}/{steps}  loss {loss.item():.4f}  "
                  f"live codes {'/'.join(f'{a}:{K}' for a in alive)}")

    # ── freeze ────────────────────────────────────────────────────────────────
    enc.eval()
    model = {
        "version": version,
        "embed_model": cfg["embed_model"],
        "levels": L,
        "codebook_k": K,
        "latent_dim": D,
        "trained_on": int(n),
        "trained_at": date.today().isoformat(),
        "enc_w": [m.weight.detach().T.cpu().tolist() for m in enc.net if isinstance(m, nn.Linear)],
        "enc_b": [m.bias.detach().cpu().tolist() for m in enc.net if isinstance(m, nn.Linear)],
        "codebooks": [c.detach().cpu().tolist() for c in codebooks],
    }
    out.write_text(json.dumps(model))
    print(f"\nFROZEN → {out}")
    print("  Retraining re-buckets every document. Bump `version` rather than overwriting.")

    # Health on the DOCUMENTS, not on X[:len(docs)] — X interleaves each doc with its own
    # chunks, so a prefix slice of it is "the first few docs and their paragraphs", which
    # reports a bucket distribution that is pure fiction.
    doc_vecs = np.array(embed(cfg, [doc_text(cfg, d) for d in docs]), dtype=np.float32)
    codes = encode_vectors(model, doc_vecs)
    used = {c[0] for c in codes}
    print(f"\n  {len(docs)} docs land in {len(used)} of {K} level-1 buckets")
    health(model, codes, K, L)


def health(model: dict, codes: list[list[int]], K: int, L: int) -> None:
    """
    Dead codes are dead bits with a different name. Report them loudly: a 16-way split that
    is really a 4-way split still produces topic_ids that look perfectly plausible.
    """
    print("\n  code usage by level (a dead code is address space you cannot use):")
    for lv in range(L):
        counts = [0] * K
        for c in codes:
            counts[c[lv]] += 1
        live = sum(1 for x in counts if x)
        bar = "".join("▁▂▃▄▅▆▇█"[min(7, x * 8 // (max(counts) + 1))] for x in counts)
        print(f"    level {lv + 1}  {live:>2}/{K} live  {bar}")


# ── assign ────────────────────────────────────────────────────────────────────


def cmd_assign(cfg: dict, args) -> None:
    model = load_codebook(cfg)
    docs = collect(cfg)
    vectors = json.loads(data_file(cfg, "vectors").read_text())

    index_path = data_file(cfg, "index")
    if not index_path.exists():
        sys.exit("no index — run `semantic_ids.py mint` first")
    by_path = {d["path"]: d for d in json.loads(index_path.read_text())["docs"]}

    keep = [d for d in docs if str(d["path"]) in by_path]
    X = np.array([vectors[by_path[str(d["path"])]["id"]] for d in keep], dtype=np.float32)
    codes = encode_vectors(model, X)

    labels = load_labels(cfg)
    stamped = 0
    for d, c in zip(keep, codes):
        d["topic_id"] = encode_topic(c, model["version"])
        d["codes"] = c
        if not d["stamp"]:
            continue
        dialect = d["dialect"] if d["dialect"] != "none" else "yaml"
        fence = d["fence"] or "---"
        sep = ": " if dialect == "yaml" else " = "
        updates = {"topic_id": [f"topic_id{sep}{quote(d['topic_id'], dialect)}"]}
        path = labels_path_for(labels, model["version"], c)
        if path:
            updates["topic_path"] = [f"topic_path{sep}{quote(path, dialect)}"]
        fm = set_fields(d["fm"], updates, dialect)
        want = f"{fence}\n{fm}\n{fence}\n{d['body']}"
        if want != d["path"].read_text(errors="replace"):
            if not args.dry_run:
                d["path"].write_text(want)
            stamped += 1

    verb = "would stamp" if args.dry_run else "stamped"
    print(f"assigned {len(keep)} topic_ids; {verb} {stamped} files")
    health(model, codes, model["codebook_k"], model["levels"])
    if not labels:
        print("\n  no bucket names yet — run `topics.py label` to make the prefix mean something")


# ── label: make the prefix mean something, in words ───────────────────────────


def labels_file(cfg: dict) -> Path:
    return cfg["_data"] / f"{cfg['_name']}.topic-labels.json"


def load_labels(cfg: dict) -> dict:
    p = labels_file(cfg)
    return json.loads(p.read_text()) if p.exists() else {}


def labels_path_for(labels: dict, version: str, codes: list[int]) -> str:
    """gpu-compute/apple-metal/shaders — as deep as we have names for."""
    parts = []
    for depth in range(1, len(codes) + 1):
        key = encode_topic(codes[:depth], version)
        if key in labels:
            parts.append(labels[key])
    return "/".join(parts)


def name_group(cfg: dict, chat: str, parent: str, group: dict[str, list[str]]) -> dict[str, str]:
    """
    Name a whole set of SIBLING buckets in one call.

    The old labeller showed the model one bucket at a time, which is why it produced
    `guitar` + `stonks` + `switchboard` → "music-production-tools". Asked what a set of
    things has in common, in isolation, a model will ALWAYS find something — it pattern-
    matches on one member and generalizes. It has no way to know that the honest answer is
    "nothing much", because it has never seen what it is supposed to contrast against.

    So: show it every sibling at once, require the names to be DISTINCT (a name that fits
    two siblings has failed at its only job), and explicitly license `mixed` for a bucket
    with no real theme. Refusing to name is a valid answer, and a taxonomy that admits its
    junk drawer is more useful than one that dresses it up.
    """
    listing = []
    for key in sorted(group):
        titles = group[key][:14]
        listing.append(f"[{key}] ({len(group[key])} docs)\n"
                       + "\n".join(f"    - {t[:80]}" for t in titles))
    scope = f"They are all sub-topics of '{parent}'. " if parent else ""
    prompt = (
        f"Below are {len(group)} clusters of documents, grouped by meaning. {scope}"
        f"Name each one.\n\n" + "\n\n".join(listing) + "\n\n"
        f"Rules:\n"
        f"- One short kebab-case slug per cluster (2-4 words), e.g. gpu-compute, rust-async.\n"
        f"- The names must DISTINGUISH the clusters from EACH OTHER. A name that could "
        f"describe two of these clusters is wrong.\n"
        f"- If a cluster has no real common theme, name it exactly `mixed`. Do not invent a "
        f"theme to be polite — `mixed` is a correct and useful answer.\n"
        f"- Name what the documents ARE, not what they might be used for.\n\n"
        f"Reply with one line per cluster, exactly:  [KEY] slug\n"
        f"Nothing else."
    )
    out = post(cfg["ollama"], "/api/generate",
               {"model": chat, "prompt": prompt, "stream": False, "think": False,
                "options": {"temperature": 0.2}})
    raw = re.sub(r"<think>.*?</think>", "", out.get("response", ""), flags=re.S)

    got: dict[str, str] = {}
    for line in raw.splitlines():
        m = re.match(r"\s*\[?([A-Za-z0-9:_-]+)\]?\s*[:=-]?\s*([a-z0-9-]+)\s*$", line.strip())
        if not m:
            continue
        key, slug = m.group(1), m.group(2).strip("-")[:40]
        if key in group and slug:
            got[key] = slug

    # Enforce distinctness ourselves rather than trusting the instruction. A duplicate name
    # is exactly the failure this whole rewrite exists to stop, so it does not get to
    # survive on the model's good intentions.
    seen: dict[str, str] = {}
    for key in sorted(got, key=lambda k: -len(group[k])):  # biggest bucket keeps the name
        slug = got[key]
        if slug in seen:
            got[key] = "mixed"
        else:
            seen[slug] = key
    return got


def cmd_label(cfg: dict, args) -> None:
    """
    Name every bucket by showing a local model the titles inside it — CONTRASTIVELY, one
    sibling set per call, so it can see what it is distinguishing between.

    The taxonomy that comes out is a controlled vocabulary DISCOVERED from the corpus's
    actual structure rather than hand-listed in an EXTRA_VOCAB. That is the tags problem
    from design.md, answering itself.
    """
    model = load_codebook(cfg)
    v = model["version"]
    docs = collect(cfg)
    vectors = json.loads(data_file(cfg, "vectors").read_text())
    by_path = {d["path"]: d for d in json.loads(data_file(cfg, "index").read_text())["docs"]}
    keep = [d for d in docs if str(d["path"]) in by_path]
    X = np.array([vectors[by_path[str(d["path"])]["id"]] for d in keep], dtype=np.float32)
    codes = encode_vectors(model, X)

    chat = cfg.get("topics", {}).get("label_model", "qwen35-cl46-abl-9b:latest")
    labels = {} if args.force else load_labels(cfg)

    # ── cohesion: STOP ASKING THE MODEL TO BE HONEST, AND MEASURE IT ─────────────
    #
    # Given a licence to answer `mixed`, the model used it zero times out of 86 — and
    # cheerfully named {guitar, stonks, switchboard, want-me-to} "audio-tools", having
    # pattern-matched on one member and generalized. A model asked what a set of things
    # has in common will ALWAYS find something. That is not a prompt bug you can fix with
    # a firmer instruction; it is what the machine is.
    #
    # So measure it instead. A real cluster is TIGHT: its documents are closer to each
    # other than two random documents are. Mean pairwise cosine within the bucket, against
    # the corpus-wide baseline. A bucket that is no tighter than chance is not a topic, and
    # it does not get a name no matter how confident the label sounded.
    #
    # This is the same instinct as every other check here: a plausible-looking output is
    # not evidence. Compute the number.
    unit = {}
    for d in keep:
        x = np.array(vectors[by_path[str(d["path"])]["id"]], dtype=np.float32)
        unit[str(d["path"])] = x / np.linalg.norm(x)
    allv = np.array(list(unit.values()))
    sims = (allv @ allv.T)[np.triu_indices(len(allv), 1)]
    baseline = float(sims.mean())
    margin = cfg.get("topics", {}).get("cohesion_margin", 0.05)

    def cohesion(paths: list[str]) -> float:
        if len(paths) < 3:
            return 1.0  # too small to judge; not evidence of incoherence
        M = np.array([unit[p] for p in paths])
        return float((M @ M.T)[np.triu_indices(len(M), 1)].mean())

    # NEGATIVE RESULT, and it is worth stating plainly: cohesion measures TIGHTNESS, and
    # tightness is not coherence.
    #
    # The 26-term AI glossary bucket scores 0.625 — BELOW the 0.637 corpus baseline. Its
    # documents are less similar to each other than two random documents are, and that is
    # CORRECT: a glossary deliberately spans a whole field (GAN, LoRA, temperature,
    # alignment). It is a real category that is genuinely not tight. Bucket F (calendar,
    # guitar, stonks, hugo) also sits below baseline, and is genuine junk. The measure
    # cannot tell them apart.
    #
    # So the override is scoped to where it is actually reliable: SMALL buckets, where a
    # low score really does mean grab-bag. On big ones the number is printed as a warning
    # and the name stands. Tuning the threshold until it agreed with my prior would have
    # been the easy move and a dishonest one.
    big = cfg.get("topics", {}).get("cohesion_trust_below", 15)

    def apply_cohesion(group_paths: dict[str, list[str]], named: dict[str, str]) -> dict:
        out = {}
        for k, slug in named.items():
            c, n = cohesion(group_paths[k]), len(group_paths[k])
            loose = c < baseline + margin
            if loose and n >= big:
                print(f"    ~ {k} cohesion {c:.3f} is loose, but {n} docs is too broad to "
                      f"judge on tightness — keeping {slug!r}")
                out[k] = slug
            elif loose:
                print(f"    ! {k} cohesion {c:.3f} < {baseline + margin:.3f} — "
                      f"overriding {slug!r} → mixed")
                out[k] = "mixed"
            else:
                out[k] = slug
        return out

    print(f"corpus baseline cohesion {baseline:.3f}; a bucket must beat "
          f"{baseline + margin:.3f} to earn a name\n")

    # Level 1: every top-level bucket is a sibling of every other. One call, all of them.
    top: dict[str, list[str]] = {}
    top_paths: dict[str, list[str]] = {}
    for d, c in zip(keep, codes):
        key = encode_topic(c[:1], v)
        top.setdefault(key, []).append(d["title"])
        top_paths.setdefault(key, []).append(str(d["path"]))
    todo = {k: t for k, t in top.items() if k not in labels and len(t) >= args.min_docs}
    if todo:
        print(f"level 1 — naming {len(todo)} sibling buckets in one call ({chat})")
        labels |= apply_cohesion(top_paths, name_group(cfg, chat, "", todo))
        for k in sorted(todo, key=lambda k: -len(todo[k])):
            print(f"  {k:<8} {len(todo[k]):>3} docs  "
                  f"{cohesion(top_paths[k]):.3f}  → {labels.get(k, '—')}")

    # Level 2+: siblings are the children of ONE parent, and the parent's name is context.
    for lvl in range(2, args.depth + 1):
        groups: dict[str, dict[str, list[str]]] = {}
        gpaths: dict[str, list[str]] = {}
        for d, c in zip(keep, codes):
            key = encode_topic(c[:lvl], v)
            groups.setdefault(encode_topic(c[: lvl - 1], v), {}).setdefault(key, []).append(d["title"])
            gpaths.setdefault(key, []).append(str(d["path"]))
        for parent, group in sorted(groups.items()):
            todo = {k: t for k, t in group.items()
                    if k not in labels and len(t) >= args.min_docs}
            if not todo:
                continue
            # A child of a `mixed` parent inherits the doubt: there is no coherent scope to
            # contrast against, so the model has nothing to differentiate within.
            pname = labels.get(parent, "")
            print(f"\nlevel {lvl} under {parent} ({pname or '—'}) — {len(todo)} siblings")
            labels |= apply_cohesion(gpaths, name_group(cfg, chat, pname, todo))
            for k in sorted(todo, key=lambda k: -len(todo[k])):
                print(f"  {k:<8} {len(todo[k]):>3} docs  "
                      f"{cohesion(gpaths[k]):.3f}  → {labels.get(k, '—')}")

    labels_file(cfg).write_text(json.dumps(labels, indent=1))
    mixed = sum(1 for x in labels.values() if x == "mixed")
    print(f"\n{len(labels)} buckets named ({mixed} honestly `mixed`) → {labels_file(cfg)}")
    print("  run `topics.py assign` to write topic_path into frontmatter")


# ── tree ──────────────────────────────────────────────────────────────────────


def cmd_tree(cfg: dict, args) -> None:
    model = load_codebook(cfg)
    labels = load_labels(cfg)
    docs = collect(cfg)
    vectors = json.loads(data_file(cfg, "vectors").read_text())
    by_path = {d["path"]: d for d in json.loads(data_file(cfg, "index").read_text())["docs"]}
    keep = [d for d in docs if str(d["path"]) in by_path]
    X = np.array([vectors[by_path[str(d["path"])]["id"]] for d in keep], dtype=np.float32)
    codes = encode_vectors(model, X)

    v = model["version"]
    tree: dict = {}
    for d, c in zip(keep, codes):
        node = tree
        for lvl in range(1, args.depth + 1):
            node = node.setdefault(encode_topic(c[:lvl], v), {"_docs": [], "_kids": {}})
            node["_docs"].append(d)
            node = node["_kids"]

    def show(node: dict, ind: int) -> None:
        for key in sorted(node, key=lambda k: -len(node[k]["_docs"])):
            n = node[key]
            name = labels.get(key, "?")
            print(f"{'  ' * ind}{key:<10} {len(n['_docs']):>3}  {name}")
            if ind + 1 < args.depth:
                show(n["_kids"], ind + 1)
            elif args.docs:
                for d in n["_docs"][:6]:
                    print(f"{'  ' * (ind + 1)}           · {d['title'][:60]}")

    print(f"{len(keep)} docs, codebook {v}\n")
    show(tree, 0)


def main() -> None:
    ap = argparse.ArgumentParser(prog="topics")
    ap.add_argument("--context", "-c")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train", help="train + FREEZE the codebook (needs torch)")
    t.add_argument("--steps", type=int, default=3000)
    t.add_argument("--force", action="store_true", help="overwrite an existing codebook")
    t.add_argument("--re-embed", action="store_true", help="re-embed chunks, ignore cache")
    t.set_defaults(fn=cmd_train)

    a = sub.add_parser("assign", help="stamp topic_id / topic_path into frontmatter")
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(fn=cmd_assign)

    l = sub.add_parser("label", help="name every bucket with a local model")
    l.add_argument("--depth", type=int, default=2)
    l.add_argument("--min-docs", type=int, default=2)
    l.add_argument("--force", action="store_true", help="re-name buckets that have names")
    l.set_defaults(fn=cmd_label)

    tr = sub.add_parser("tree", help="print the taxonomy")
    tr.add_argument("--depth", type=int, default=2)
    tr.add_argument("--docs", action="store_true", help="list documents at the leaves")
    tr.set_defaults(fn=cmd_tree)

    args = ap.parse_args()
    args.fn(load_context(args.context), args)


if __name__ == "__main__":
    main()
