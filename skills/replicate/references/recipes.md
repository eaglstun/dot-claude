# Invocation recipes

Worked examples, the permission-friendly invocation rules, runtime quick pointers,
and how to extend the skill to a new modality.

## Worked examples

Example — text-to-video with Seedance:

```bash
python scripts/run_model.py bytedance/seedance-2.0 \
    --input '{"prompt": "a sea turtle gliding over a coral reef at sunset, cinematic", "duration": 5, "aspect_ratio": "16:9"}' \
    --output ./out/
```

Example — text-to-image with Flux Schnell (cheap, fast, good for quick iterations or tests):

```bash
python scripts/run_model.py black-forest-labs/flux-schnell \
    --input '{"prompt": "a koala holding a lightsaber, studio ghibli style"}' \
    --output ./out/
```

Prefer `--input-file path.json` for non-trivial inputs. Write the JSON via the `Write` tool first, then invoke the script with only literal args — no shell expansion. This keeps every invocation prefix-matchable by Claude Code's permission system, so `Bash(python scripts/run_model.py:*)` never triggers a prompt.

```bash
python scripts/run_model.py bytedance/seedance-2.0 \
    --input-file input.json \
    --output ./out/
```

## Permission-friendly invocations (avoid shell expansion)

Claude Code's Bash permission matcher refuses to prefix-match commands containing `$VAR`, `$(...)`, backticks, pipes, redirects, or `;`/`&&`. Each such command triggers a per-invocation permission prompt even when `Bash(python scripts/run_model.py:*)` is allowlisted.

**Rule:** when calling `run_model.py`, pass **literal values only** — no command substitution, no `$VAR`, no `~` (expand it to an absolute path in the tool call itself), no pipes/redirects. For anything non-trivial, use `--input-file` with a JSON file written via the `Write` tool.

```bash
# bad  — shell expansion, prompts every time
python scripts/run_model.py black-forest-labs/flux-schnell --input "{\"prompt\": \"$MY_PROMPT\"}" --output ~/out/

# good — all literal, prefix-matches cleanly
python scripts/run_model.py black-forest-labs/flux-schnell --input-file ~/work/input.json --output ~/work/out/
```

## Runtime quick pointers

Full detail in `references/runtime.md`; the highlights:

- File outputs auto-expire after ~1 hour — save or use immediately.
- Every run writes a `.meta.json` sidecar; metadata is also embedded into PNG/JPG/WebP/MP4/WebM/MOV/MKV/WAV/MP3 files where supported. Pass `--no-metadata` or `--no-sidecar` to opt out.
- Bare slugs (`owner/name`) auto-resolve to a pinned version hash — handles the 404-on-bare-slug bug some older models have.

## Extending to other modalities

This skill is intentionally modality-agnostic. Category selection files already exist for **image**, **video**, **audio**, and **segmentation**. When the user first needs a category that doesn't have one (music, text/LLM, embedding, or anything else), create `references/<category>-models.md` with the same shape as `video-models.md`:

- A short selection table (use case → model)
- Per-model input schemas (what's required, what's optional, with ranges)
- Any modality-specific gotchas
- Then add the new category file to the "References - load on demand" list in `SKILL.md`, and a line to `references/models/INDEX.md` if you add per-model deep-dives.

The `run_model.py` script itself never needs to change — it handles file outputs, dict outputs, list outputs, and iterator (streaming) outputs uniformly.
