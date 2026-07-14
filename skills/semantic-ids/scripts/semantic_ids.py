#!/usr/bin/env python3
"""
Semantic IDs — a 192-bit, 32-character base64url string whose bits ARE the meaning
of a document. Two documents about the same thing get IDs that are close in Hamming
distance (count of differing bits), so "find related" is an XOR and a popcount. No
vector database, no server, nothing to deploy.

    ┌──────────────── 172 bits semantic ───────────────┬── 16b day ──┬─ 4b hash ─┐
    │  sign(v[i] - frozenMean[i]),  i = 0..171         │ since epoch │ tiebreak  │
    └──────────────────────────────────────────────────┴─────────────┴───────────┘
    192 bits = 24 bytes = exactly 32 base64url chars, no padding

This is the CONTEXT-DRIVEN engine. It knows nothing about any particular corpus; a
context TOML says where the files are, how to read a title/summary out of them, and
where that corpus's FROZEN MEAN lives. See contexts/claude-home.toml.

    semantic_ids.py mint     [--context X] [--force] [--dry-run]
    semantic_ids.py query    [--context X] "how do I transcribe a video"
    semantic_ids.py near     [--context X] path/to/file.md
    semantic_ids.py stats    [--context X]

Two properties this guarantees, because an ID committed to git is forever:

  IDEMPOTENT  Re-running produces byte-identical IDs. The 4 "random" tiebreak bits
              come from a content hash, not a PRNG. Documents that already have an
              id keep it untouched unless you pass --force.

  STABLE      The mean vector is computed ONCE per context, frozen to disk, and never
              recomputed. Binarization is sign(v - mean), so if the mean drifts as the
              corpus grows, every previously-issued ID silently becomes wrong. No error,
              no warning, just quietly incomparable numbers that still look plausible.

Requires Ollama with an embedding model. Standard library only.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import tomllib
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent

# ── the bit layout ────────────────────────────────────────────────────────────
#
# Hex spends 4 bits per character — one nibble — and throws away the other half of every
# character's capacity. Base64 spends 6. At a fixed 32-character width that is the
# difference between 128 bits and 192, i.e. 108 semantic bits vs 172, for free.
#
# The sizes land exactly: 192 bits = 24 bytes, and base64 packs 3 bytes into 4 chars,
# so 24 bytes is precisely 32 characters with no padding and no ragged edge.
#
# 64 symbols rather than 62 (plain alphanumerics) because 64 is a power of two: encoding
# is then pure bit-shifting instead of bignum long division. base64URL's `-` and `_`
# (rather than base64's `+` and `/`) keep the IDs safe in URLs and filenames.

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

SEMANTIC_BITS = 172
DAY_BITS = 16
HASH_BITS = 4
TOTAL_BITS = SEMANTIC_BITS + DAY_BITS + HASH_BITS  # 192
ID_CHARS = TOTAL_BITS // 6  # 32

EPOCH = date(2026, 1, 1)

TAIL_BITS = DAY_BITS + HASH_BITS
SEMANTIC_MASK = ((1 << SEMANTIC_BITS) - 1) << TAIL_BITS


# ── ollama ────────────────────────────────────────────────────────────────────


def post(host: str, path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{host}{path}",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.URLError as e:
        sys.exit(f"ollama unreachable at {host}: {e}\nIs `ollama serve` running?")


def embed(cfg: dict, texts: list[str], *, query: bool = False) -> list[list[float]]:
    """nomic wants a task prefix; documents and queries land in slightly different
    regions of the space on purpose, so a query embedded as a document ranks worse."""
    prefix = "search_query: " if query else "search_document: "
    out = []
    batch = 32
    for i in range(0, len(texts), batch):
        chunk = texts[i : i + batch]
        r = post(
            cfg["ollama"],
            "/api/embed",
            {"model": cfg["embed_model"], "input": [prefix + t for t in chunk]},
        )
        out.extend(r["embeddings"])
    return out


# ── the ID ────────────────────────────────────────────────────────────────────


def encode64(bits: int) -> str:
    return "".join(
        ALPHABET[(bits >> (TOTAL_BITS - 6 * (i + 1))) & 0x3F] for i in range(ID_CHARS)
    )


def decode64(text: str) -> int:
    bits = 0
    for ch in text:
        bits = (bits << 6) | ALPHABET.index(ch)
    return bits


def binarize(vector: list[float], mean: list[float]) -> int:
    """
    sign(v - mean) over the leading SEMANTIC_BITS dimensions.

    Mean-centering is NOT optional. Raw embedding dims are not zero-centered — some are
    positive for essentially every input — so a naive sign() emits bits that are constant
    across the whole corpus. Dead bits: address space you paid for and cannot use.
    Measured on a real corpus, one subtraction recovered ~35 bits of real capacity.
    """
    bits = 0
    for i in range(SEMANTIC_BITS):
        bits = (bits << 1) | (1 if vector[i] - mean[i] > 0 else 0)
    return bits


def mint(vector: list[float], mean: list[float], days: int, text: str) -> str:
    bits = binarize(vector, mean)
    bits = (bits << DAY_BITS) | max(0, min(days, (1 << DAY_BITS) - 1))
    # Deterministic tiebreak, so re-running never changes an ID.
    tie = int(hashlib.sha256(text.encode()).hexdigest(), 16) & ((1 << HASH_BITS) - 1)
    return encode64((bits << HASH_BITS) | tie)


def hamming(a: str, b: str) -> int:
    """
    Semantic distance. Masks off the day/tiebreak tail — to Hamming those bits are pure
    NOISE, and two identical docs published a year apart differ by ~10 of them for no
    semantic reason.

    Note there is no dash-stripping here. `-` is a legitimate base64url character. The
    reflexive `.replace("-", "")` that a UUID-shaped string invites would delete real
    bits out of the middle of the ID.
    """
    return bin((decode64(a) ^ decode64(b)) & SEMANTIC_MASK).count("1")


def hamming_bits(a_bits: int, b: str) -> int:
    """Distance from an already-binarized query (no tail) to a full ID string."""
    return bin(a_bits ^ (decode64(b) >> TAIL_BITS)).count("1")


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


# ── frontmatter ───────────────────────────────────────────────────────────────

YAML_FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)
TOML_FM = re.compile(r"\A\+\+\+\n(.*?)\n\+\+\+\n", re.S)


def split_fm(text: str, dialect: str) -> tuple[str, str, str] | None:
    """→ (fence, frontmatter_text, body) or None if there is no frontmatter."""
    if dialect == "yaml":
        m = YAML_FM.match(text)
        return ("---", m.group(1), text[m.end() :]) if m else None
    if dialect == "toml":
        m = TOML_FM.match(text)
        return ("+++", m.group(1), text[m.end() :]) if m else None
    return None


def parse_fm(fm_text: str, dialect: str) -> dict:
    """
    A deliberately small frontmatter reader. It handles exactly what these corpora use:
    top-level scalars, quoted scalars, and YAML folded/literal blocks (`>-`, `|`), which
    is how every SKILL.md writes its multi-line description. It is not a YAML parser and
    is not trying to be — nested structures are ignored, not mangled.
    """
    fields: dict[str, str] = {}
    lines = fm_text.splitlines()
    i = 0
    sep = ":" if dialect == "yaml" else "="
    key_re = re.compile(rf"^([A-Za-z_][A-Za-z0-9_-]*)\s*{re.escape(sep)}\s*(.*)$")
    while i < len(lines):
        m = key_re.match(lines[i])
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2).strip()
        # A value can continue onto INDENTED lines below it: a folded/literal block
        # (`>-`, `|`), or a list the formatter wrapped or expanded. Miss those and the
        # continuation is orphaned when the key is replaced — which produces duplicate
        # junk and invalid YAML. Consume them.
        if dialect == "yaml" and (value[:1] in (">", "|") or value == ""):
            block, i = [], i + 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            fields[key] = " ".join(b for b in block if b)
            continue
        fields[key] = unquote(value)
        i += 1
    return fields


def yaml_list(items: list[str]) -> list[str]:
    """
    A YAML block sequence, not a flow list.

    This is not a style preference. An inline `key: ["a", "b"]` of two 32-char IDs is 85
    characters, which is past a markdown formatter's 80-column print width — so prettier
    wraps it onto a continuation line, and the file no longer round-trips through a
    line-based editor. The block form is already the formatter's canonical output at any
    width, so it survives being formatted. Write what the formatter would have written.
    """
    return [f"  - {q}" for q in items]


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return v


def quote(s: str, dialect: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def set_fields(fm_text: str, updates: dict[str, list[str]], dialect: str) -> str:
    """
    Replace or append a key, preserving everything else VERBATIM.

    We do not round-trip through a YAML/TOML serializer on purpose. Reserializing this
    frontmatter would reflow every folded description block in the corpus and turn a
    two-line ID stamp into a thousand-line diff.

    `updates` maps a key to the FULL list of lines it should become — so a key can span
    several lines. Replacing one deletes its indented continuation lines too. Skipping
    that step is how a formatter-wrapped list leaves an orphaned fragment behind, which
    is invalid YAML and silently breaks whatever reads the frontmatter.
    """
    lines = fm_text.splitlines()
    for key, new_lines in updates.items():
        pat = re.compile(rf"^{re.escape(key)}\s*{':' if dialect == 'yaml' else '='}")
        for i, existing in enumerate(lines):
            if not pat.match(existing):
                continue
            j = i + 1
            while j < len(lines) and lines[j].startswith((" ", "\t")):
                j += 1  # this key's continuation lines — they go with it
            lines[i:j] = new_lines
            break
        else:
            lines.extend(new_lines)
    return "\n".join(lines)


# ── reading a document out of a file ──────────────────────────────────────────

H1 = re.compile(r"^#\s+(.+?)\s*$", re.M)


def first_paragraph(body: str, limit: int = 500) -> str:
    """First real prose paragraph: not a heading, list, fence, table, or blockquote."""
    para: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            if para:
                break
            continue
        if line.startswith(("#", "```", "|", ">", "- ", "* ", "<!--")) or re.match(r"^\d+\.", line):
            if para:
                break
            continue
        para.append(line)
    return re.sub(r"\s+", " ", " ".join(para))[:limit]


def read_doc(path: Path, src: dict, root: Path) -> dict | None:
    text = path.read_text(errors="replace")
    dialect = src.get("frontmatter", "none")
    parts = split_fm(text, dialect)

    if dialect != "none" and parts is None:
        return None  # declared frontmatter, has none — not a document

    if parts:
        fence, fm_text, body = parts
        fields = parse_fm(fm_text, dialect)
        title = fields.get(src.get("title_field", "title"), "") or path.stem
        summary = fields.get(src.get("summary_field", "description"), "")
    else:
        # `frontmatter = "none"` means "the title and summary come from the BODY" — it does
        # NOT mean the file can't have frontmatter. If we stamped this file on a previous
        # run, it has a block now, and we must SEE it. Miss it and two things break at
        # once: the existing semantic_id is invisible (so we stamp again, prepending a
        # second block, forever), and the block's own text leaks into the embedded summary.
        # Consuming every leading block also repairs a file already doubled up this way.
        # Keep the block TEXT, not just its parsed fields. A writer that only manages some
        # of the keys (topics.py writes topic_id and nothing else) does set_fields(d["fm"])
        # — so if fm is empty it rebuilds the frontmatter from scratch and silently DELETES
        # every key it doesn't know about. That wiped semantic_id out of 232 files exactly
        # once, and the only reason it was recoverable is that the index still had them.
        fields, blocks = {}, []
        body = text
        while (leading := split_fm(body, "yaml")) is not None:
            _, block, body = leading
            fields |= parse_fm(block, "yaml")
            blocks.append(block)
        fm_text = "\n".join(blocks)
        fence = "---" if blocks else ""

        h1 = H1.search(body)
        title = h1.group(1) if h1 else path.stem.replace("-", " ")
        summary = first_paragraph(body[h1.end() :] if h1 else body)
        # A bare H1 like "Overview" is not distinctive across a dozen library folders.
        # The containing directory IS semantic (cuda vs rust vs metal), so it goes in.
        rel_parent = path.parent.relative_to(root)
        if rel_parent.parts:
            title = f"{rel_parent.parts[-1]}: {title}"

    if not summary.strip():
        return None  # nothing to embed but a filename — an ID here would be a lie

    return {
        "path": path,
        "source": src["name"],
        "dialect": dialect,
        "stamp": bool(src.get("stamp", False)),
        "fields": fields,
        "fm": fm_text,
        "fence": fence,
        "body": body,
        "title": title.strip(),
        "summary": summary.strip(),
    }


def days_since_epoch(fields: dict, field: str | None) -> int:
    """Undated docs get day 0 — stable, and honest about having no date."""
    if not field:
        return 0
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", fields.get(field, "") or "")
    if not m:
        return 0
    return max(0, (date(*map(int, m.groups())) - EPOCH).days)


# ── contexts ──────────────────────────────────────────────────────────────────


def find_context(name: str | None) -> Path:
    """
    Resolution order, most specific first:
      --context /path/to/x.toml   an explicit file
      --context name              contexts/<name>.toml in the skill
      (nothing)                   ./.claude/semantic-ids.toml walking up from cwd,
                                  else the user-level claude-home context
    """
    if name:
        p = Path(name).expanduser()
        if p.is_file():
            return p
        p = SKILL / "contexts" / f"{name}.toml"
        if p.is_file():
            return p
        sys.exit(f"no context named {name!r} (looked for a file, and {p})")

    for d in [Path.cwd(), *Path.cwd().parents]:
        p = d / ".claude" / "semantic-ids.toml"
        if p.is_file():
            return p
    return SKILL / "contexts" / "claude-home.toml"


def load_context(name: str | None) -> dict:
    cfg_path = find_context(name)
    cfg = tomllib.loads(cfg_path.read_text())
    base = cfg_path.parent

    def resolve(p: str) -> Path:
        q = Path(p).expanduser()
        return q if q.is_absolute() else (base / q).resolve()

    cfg["_path"] = cfg_path
    cfg["_name"] = cfg.get("name", cfg_path.stem)
    cfg.setdefault("ollama", "http://127.0.0.1:11434")
    cfg.setdefault("embed_model", "nomic-embed-text")
    cfg.setdefault("related_count", 6)
    cfg.setdefault("related_max_distance", 72)
    cfg["_data"] = resolve(cfg.get("data_dir", "../data"))
    for s in cfg["source"]:
        s["_root"] = resolve(s["root"])
    return cfg


def data_file(cfg: dict, kind: str) -> Path:
    return cfg["_data"] / f"{cfg['_name']}.{kind}.json"


def collect(cfg: dict) -> list[dict]:
    docs, seen = [], set()
    for src in cfg["source"]:
        root: Path = src["_root"]
        if not root.exists():
            print(f"  ! source {src['name']!r}: {root} does not exist, skipping")
            continue
        for path in sorted(root.glob(src.get("glob", "**/*.md"))):
            if not path.is_file() or path in seen:
                continue
            for pat in src.get("exclude", []):
                if path.match(pat):
                    break
            else:
                doc = read_doc(path, src, root)
                if doc:
                    seen.add(path)
                    docs.append(doc)
    return docs


def doc_text(cfg: dict, d: dict) -> str:
    """
    What we actually embed: title + summary (+ tags). NOT the body.

    An embedding is a fixed-size container — the same 768 floats whether you hand it a
    sentence or an entire manual. Feed it a whole document and you get the CENTROID of
    everything in it: a vector that is near everything and specifically about nothing.
    One embedding should hold about one idea. A skill's `description` is already the best
    one-sentence statement of what it is for, which is exactly why nothing here tries to
    generate a summary.
    """
    tags = d.get("tags") or []
    text = f"{d['title']}. {d['summary']}"
    if tags:
        text += f" Topics: {', '.join(tags)}."
    return text


# ── tags (opt-in, controlled vocabulary only) ─────────────────────────────────


def generate_tags(cfg: dict, d: dict, vocab: list[str]) -> list[str]:
    """
    Tags come from a CONTROLLED VOCABULARY, never the model's imagination.

    Free-form tag generation was tried and produced `aspartame-grade-ml`, `sepahora-bot`,
    and `three-hours-150-dollars` — the model shredding title fragments into tag-shaped
    noise — then bolted `attention-mechanism` onto essays about labour policy. Tags feed
    the embedding text, so junk tags mean junk vectors: strictly worse than no tags.
    A fixed list means the model CHOOSES rather than INVENTS. Anything off-list is
    dropped on the floor. That is the whole point.
    """
    tcfg = cfg["tags"]
    n = tcfg.get("count", 6)
    prompt = (
        f"Choose the tags that describe this document.\n\n"
        f"Title: {d['title']}\nSummary: {d['summary']}\n\n"
        f"Excerpt:\n{d['body'][:1200]}\n\n"
        f"ALLOWED TAGS (you may ONLY use tags from this list):\n{', '.join(vocab)}\n\n"
        f"Pick between 2 and {n} tags that genuinely describe this document. Fewer is "
        f"better than wrong. Do NOT invent tags. Do NOT pick a tag because it sounds "
        f"technical — only if the document is actually about it.\n"
        f"Respond with ONLY a comma-separated list from the allowed tags, nothing else."
    )
    out = post(
        cfg["ollama"],
        "/api/generate",
        {
            "model": tcfg["chat_model"],
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1},
        },
    )
    raw = re.sub(r"<think>.*?</think>", "", out.get("response", ""), flags=re.S)
    allowed, tags = set(vocab), []
    for t in re.split(r"[,\n]", raw):
        t = t.strip().strip("-*`.").lower()
        if t in allowed and t not in tags:
            tags.append(t)
    return tags[:n]


# ── commands ──────────────────────────────────────────────────────────────────


def cmd_mint(cfg: dict, args) -> None:
    docs = collect(cfg)
    if not docs:
        sys.exit("no documents found — check the [[source]] roots and globs")
    print(f"context {cfg['_name']!r} ({cfg['_path']})")
    for src in cfg["source"]:
        n = sum(1 for d in docs if d["source"] == src["name"])
        mode = "stamped" if src.get("stamp") else "index only"
        print(f"  {src['name']:<12} {n:>4} docs  ({mode})")

    index_path = data_file(cfg, "index")
    prior = {}
    if index_path.exists():
        prior = {e["path"]: e for e in json.loads(index_path.read_text())["docs"]}

    def key(d: dict) -> str:
        return str(d["path"])

    # ── tags ──────────────────────────────────────────────────────────────────
    if "tags" in cfg:
        vocab = sorted(set(cfg["tags"]["vocab"]))
        need = [
            d
            for d in docs
            if args.force
            or not (d["fields"].get("tags") or prior.get(key(d), {}).get("tags"))
        ]
        print(f"\ntagging {len(need)} docs with {cfg['tags']['chat_model']} "
              f"(controlled vocabulary of {len(vocab)}; off-list is dropped)")
        for i, d in enumerate(need, 1):
            d["tags"] = generate_tags(cfg, d, vocab)
            print(f"  [{i}/{len(need)}] {d['title'][:44]:44} → {', '.join(d['tags'])}")
        for d in docs:
            if "tags" not in d:
                d["tags"] = prior.get(key(d), {}).get("tags") or []

    for d in docs:
        d["text"] = doc_text(cfg, d)

    print(f"\nembedding {len(docs)} docs with {cfg['embed_model']}...")
    vectors = embed(cfg, [d["text"] for d in docs])
    for d, v in zip(docs, vectors):
        d["vector"] = v

    # ── the frozen mean ───────────────────────────────────────────────────────
    mean_path = data_file(cfg, "mean")
    if mean_path.exists():
        model = json.loads(mean_path.read_text())
        if model.get("embed_model") != cfg["embed_model"]:
            sys.exit(
                f"frozen mean was built with {model.get('embed_model')!r}, not "
                f"{cfg['embed_model']!r} — every ID would be incomparable. Refusing."
            )
        mean = model["mean"]
        print(f"using FROZEN mean ({model['trained_on']} docs, {model['trained_at']})")
    else:
        dims = len(vectors[0])
        mean = [sum(v[i] for v in vectors) / len(vectors) for i in range(dims)]
        model = {
            "embed_model": cfg["embed_model"],
            "semantic_bits": SEMANTIC_BITS,
            "day_bits": DAY_BITS,
            "hash_bits": HASH_BITS,
            "epoch": EPOCH.isoformat(),
            "trained_on": len(docs),
            "trained_at": date.today().isoformat(),
            "mean": mean,
        }
        print(f"computing mean from {len(docs)} docs and FREEZING it → {mean_path}")
        print("  (never recompute this: every existing ID would silently become wrong)")
        if not args.dry_run:
            mean_path.parent.mkdir(parents=True, exist_ok=True)
            mean_path.write_text(json.dumps(model))

    # ── mint ──────────────────────────────────────────────────────────────────
    date_field = cfg.get("date_field")
    minted = 0
    for d in docs:
        existing = d["fields"].get("semantic_id") or prior.get(key(d), {}).get("id", "")
        if existing and not args.force:
            d["id"], d["fresh"] = existing, False
            continue
        d["id"] = mint(d["vector"], mean, days_since_epoch(d["fields"], date_field), d["text"])
        d["fresh"] = True
        minted += 1

    # ── related ───────────────────────────────────────────────────────────────
    # Unlike the IDs, these are recomputed for every doc on every run, and must be: a new
    # doc is a new neighbour for one minted a year ago. Rewriting a derived list of paths
    # cannot corrupt an ID, so it is safe.
    limit, count = cfg["related_max_distance"], cfg["related_count"]
    for d in docs:
        near = sorted(((hamming(d["id"], o["id"]), o) for o in docs if o is not d), key=lambda x: x[0])
        d["related"] = [
            {"id": o["id"], "path": str(o["path"]), "title": o["title"], "distance": dist}
            for dist, o in near[:count]
            if dist <= limit
        ]

    # ── write ─────────────────────────────────────────────────────────────────
    # Stamping converges the FILE to the index. It is deliberately not tied to whether the
    # ID was freshly minted (flipping a source's `stamp` to true must write the IDs it
    # already has), and the "does this need writing?" test is a comparison of the rendered
    # file against the bytes on disk — not a check of some field we hope is in sync. That
    # is what makes a re-run a genuine no-op, and what lets a malformed file self-repair.
    stamped = 0
    for d in docs:
        if not d["stamp"]:
            continue
        # A source with `frontmatter = "none"` has no fence to edit, so stamping PREPENDS
        # a block — a real mutation of a file that had none, allowed because the context
        # asked for it.
        dialect = d["dialect"] if d["dialect"] != "none" else "yaml"
        fence = d["fence"] or ("---" if dialect == "yaml" else "+++")
        def lst(key: str, items: list[str]) -> list[str]:
            qs = [quote(i, dialect) for i in items]
            if dialect == "toml":
                return [f"{key} = [" + ", ".join(qs) + "]"]
            if not qs:
                # An empty block sequence is not empty — a bare `key:` parses as NULL, not
                # as []. A document with no neighbour inside the cutoff (switchboard) gets
                # an explicit empty flow list, which is short enough that no formatter
                # wraps it.
                return [f"{key}: []"]
            return [f"{key}:", *yaml_list(qs)]  # block form — survives a formatter

        updates: dict[str, list[str]] = {"semantic_id": [f"semantic_id: {quote(d['id'], dialect)}"]}
        if dialect == "toml":
            updates["semantic_id"] = [f"semantic_id = {quote(d['id'], dialect)}"]
        if d.get("tags"):
            updates["tags"] = lst("tags", d["tags"])

        # related_ids holds IDs, not paths — a path moves the day you rename a folder, and
        # an ID doesn't. Resolve one back to a file through the index.
        #
        # Unlike semantic_id, this list is DERIVED and is rewritten on every run, and it
        # must be: a new document is a new neighbour for one minted a year ago. Rewriting
        # a derived list cannot corrupt an ID, so this is safe — it is the one thing here
        # that is allowed to churn.
        n = cfg.get("related_stamp", 0)
        if n:
            updates["related_ids"] = lst("related_ids", [r["id"] for r in d["related"][:n]])

        fm = set_fields(d["fm"], updates, dialect)
        want = f"{fence}\n{fm}\n{fence}\n{d['body']}"
        if want == d["path"].read_text(errors="replace"):
            continue
        if not args.dry_run:
            d["path"].write_text(want)
        stamped += 1

    index = {
        "context": cfg["_name"],
        "embed_model": cfg["embed_model"],
        "semantic_bits": SEMANTIC_BITS,
        "generated": date.today().isoformat(),
        "docs": [
            {
                "id": d["id"],
                # topic_id is owned by topics.py and merely carried here, so that `query
                # --under` can scope by prefix without loading a codebook. mint never
                # computes it and never writes it to a file.
                "topic_id": d["fields"].get("topic_id", ""),
                "topic_path": d["fields"].get("topic_path", ""),
                "path": str(d["path"]),
                "source": d["source"],
                "title": d["title"],
                "summary": d["summary"],
                "tags": d.get("tags") or [],
                "related": d["related"],
            }
            for d in docs
        ],
    }
    vectors_out = {d["id"]: d["vector"] for d in docs}
    if not args.dry_run:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(index, indent=1))
        data_file(cfg, "vectors").write_text(json.dumps(vectors_out))

    verb = "would stamp" if args.dry_run else "stamped"
    print(f"\nminted {minted} new IDs; {verb} {stamped} files; indexed {len(docs)}")
    if not args.dry_run:
        print(f"  → {index_path}")

    print("\nnearest neighbours, from the ID strings alone:")
    for d in docs[:5]:
        print(f"\n  {d['title']}\n  {d['id']}")
        for r in d["related"][:3]:
            print(f"    {r['distance']:3d} bits  {r['title']}")


def load_index(cfg: dict) -> tuple[list[dict], dict]:
    p = data_file(cfg, "index")
    if not p.exists():
        sys.exit(f"no index for context {cfg['_name']!r} — run `mint` first")
    return json.loads(p.read_text())["docs"], json.loads(data_file(cfg, "mean").read_text())


def cmd_query(cfg: dict, args) -> None:
    """
    Two-stage retrieval, which is the correct architecture and the whole reason the IDs
    are worth having.

    STAGE 1 — sweep with the bits. 172 bits is a COARSE instrument: a superb candidate
    generator and a mediocre ranker. Its only job is to not LOSE the right answer.

    STAGE 2 — rescore the shortlist with the full-precision float vectors. Expensive and
    precise, and it only ever touches the survivors. Measured elsewhere: this recovers
    100% of the answer an exhaustive float scan would give, at a fraction of the reads.
    """
    docs, model = load_index(cfg)
    query = " ".join(args.text)

    # --under is the capability the whole topic_id hierarchy exists to provide: scope the
    # search to a subtree by STRING PREFIX, with no distance computation at all. This is
    # precisely what design.md proves you cannot do with the sign-based semantic_id, where
    # one flipped high bit throws a document to the far end of the sort order.
    if args.under:
        want = args.under if ":" in args.under else f"v1:{args.under}"
        docs = [d for d in docs if (d.get("topic_id") or "").startswith(want)]
        if not docs:
            sys.exit(f"no documents under topic {want!r} — see `topics.py tree`")
        print(f"[scoped to {want} — {len(docs)} docs]")

    qv = embed(cfg, [query], query=True)[0]
    qbits = binarize(qv, model["mean"])

    ranked = sorted(((hamming_bits(qbits, d["id"]), d) for d in docs), key=lambda x: x[0])
    shortlist = ranked[: args.shortlist]

    if not args.no_rescore:
        vectors = json.loads(data_file(cfg, "vectors").read_text())
        scored = sorted(
            ((cosine(qv, vectors[d["id"]]), dist, d) for dist, d in shortlist),
            key=lambda x: -x[0],
        )
    else:
        scored = [(0.0, dist, d) for dist, d in shortlist]

    print(f'"{query}"\n')
    for score, dist, d in scored[: args.n]:
        s = f"{score:.3f}" if not args.no_rescore else "  -  "
        print(f"  {s}  {dist:3d}b  [{d['source']}] {d['title']}")
        print(f"                {d['path']}")


def cmd_near(cfg: dict, args) -> None:
    docs, _ = load_index(cfg)
    target = str(Path(args.path).expanduser().resolve())
    hit = next((d for d in docs if d["path"] == target), None)
    if not hit:
        hit = next((d for d in docs if target in d["path"]), None)
    if not hit:
        sys.exit(f"{args.path} is not in the {cfg['_name']!r} index")
    print(f"{hit['title']}\n{hit['id']}\n")
    for r in hit["related"][: args.n]:
        print(f"  {r['distance']:3d} bits  {r['title']}\n            {r['path']}")


def cmd_stats(cfg: dict, args) -> None:
    """
    A health check on the bits themselves. Two numbers matter:

    DEAD BITS — a bit that is identical on every document carries exactly zero
    information. Any dead bit means the mean is wrong for this corpus.

    MEAN PAIR DISTANCE — should sit at ~half of SEMANTIC_BITS (86 of 172). Two unrelated
    documents are a coin flip, as they should be. If it is far below that, the corpus is
    monotonous and the IDs are not discriminating.
    """
    docs, _ = load_index(cfg)
    ids = [d["id"] for d in docs]
    ones = [0] * SEMANTIC_BITS
    for i in ids:
        bits = decode64(i) >> TAIL_BITS
        for b in range(SEMANTIC_BITS):
            ones[SEMANTIC_BITS - 1 - b] += (bits >> b) & 1

    n = len(ids)
    dead = sum(1 for o in ones if o in (0, n))
    skew = sum(abs(o / n - 0.5) for o in ones) / SEMANTIC_BITS
    pairs = [hamming(a, b) for x, a in enumerate(ids) for b in ids[x + 1 :]]
    pairs.sort()
    print(f"context {cfg['_name']!r}: {n} docs, {SEMANTIC_BITS} semantic bits\n")
    print(f"  dead bits          {dead} / {SEMANTIC_BITS}   (must be 0)")
    print(f"  avg skew from 50/50  {skew:.1%}")
    print(f"  mean pair distance {sum(pairs) / len(pairs):.1f} bits "
          f"(chance = {SEMANTIC_BITS / 2:.0f})")
    print(f"  5th percentile     {pairs[len(pairs) // 20]} bits  "
          f"← a sane related_max_distance")
    print(f"  closest pair       {pairs[0]} bits")
    if dead:
        print("\n  ! dead bits present — the frozen mean does not fit this corpus.")

    # ── integrity: does every stamped related_id point at a document that exists? ──
    #
    # related_ids are a DERIVED cache, so they go stale the moment a document is deleted
    # and stay stale until the next mint. That is tolerable, but only if you can SEE it —
    # a dangling ID is invisible by construction, since a 32-char base64 string that
    # resolves to nothing looks exactly like one that resolves to something.
    known = set(ids)
    dangling, collisions = [], collections.Counter(ids)
    for d in docs:
        for r in d["related"]:
            if r["id"] not in known:
                dangling.append((d["path"], r["id"]))
    dupes = [i for i, c in collisions.items() if c > 1]

    # This checks every neighbour link in the INDEX, which is a superset of the first N
    # that get stamped into each file as `related_ids`. Zero dangling here means zero
    # dangling there.
    total = sum(len(d["related"]) for d in docs)
    stamp_n = cfg.get("related_stamp", 0)
    print(f"\n  neighbour links    {total} in index "
          f"({sum(min(len(d['related']), stamp_n) for d in docs)} stamped as related_ids), "
          f"{len(dangling)} dangling")
    for path, rid in dangling[:10]:
        print(f"    ! {rid} → nothing, in {path}")
    if dangling:
        print("    run `mint` to rebuild the neighbour lists.")
    if dupes:
        print(f"\n  ! {len(dupes)} ID COLLISIONS — two documents minted to the same bits.")
        for i in dupes[:5]:
            print(f"    {i}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="semantic_ids")
    ap.add_argument("--context", "-c", help="context name or path to a context .toml")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("mint", help="embed, mint IDs, stamp frontmatter, write the index")
    m.add_argument("--force", action="store_true", help="re-mint IDs that already exist")
    m.add_argument("--dry-run", action="store_true", help="report, write nothing")
    m.set_defaults(fn=cmd_mint)

    q = sub.add_parser("query", help="semantic search over the index")
    q.add_argument("text", nargs="+")
    q.add_argument("-n", type=int, default=8, help="results to show")
    q.add_argument("--shortlist", type=int, default=40, help="stage-1 candidates to rescore")
    q.add_argument("--no-rescore", action="store_true", help="bits only, skip float rescore")
    q.add_argument("--under", help="scope to a topic_id prefix, e.g. --under C or --under CM")
    q.set_defaults(fn=cmd_query)

    nr = sub.add_parser("near", help="nearest neighbours of a file")
    nr.add_argument("path")
    nr.add_argument("-n", type=int, default=6)
    nr.set_defaults(fn=cmd_near)

    st = sub.add_parser("stats", help="bit health: dead bits, skew, distance distribution")
    st.set_defaults(fn=cmd_stats)

    args = ap.parse_args()
    args.fn(load_context(args.context), args)


if __name__ == "__main__":
    main()
