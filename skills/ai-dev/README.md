# ai-dev

A personal Claude Code skill that holds a small, curated **glossary of AI/ML development
terms** — one tight paragraph per concept, kept short so it's quick to refer to mid-task.
It's a lookup reference, not a general AI-dev assistant.

## Usage

`SKILL.md` is the entry point. It's deliberately scoped to trigger **only** when you
explicitly ask for the meaning of a term that has an entry (e.g. _"what's GGUF"_,
_"define latent space"_) — not just because some task mentions AI in passing. On a match,
Claude loads the one glossary file it needs; each is self-contained.

You can also just open the files directly — they're plain Markdown under
[`references/glossary/`](references/glossary/).

## Glossary

| Term         | File                                                              | One-liner                                               |
| ------------ | ----------------------------------------------------------------- | ------------------------------------------------------- |
| GGUF         | [`glossary/gguf.md`](references/glossary/gguf.md)                 | llama.cpp single-file format for quantized local LLMs   |
| MLX          | [`glossary/mlx.md`](references/glossary/mlx.md)                   | Apple-silicon ML framework; the Mac answer to GGUF      |
| Latent space | [`glossary/latent-space.md`](references/glossary/latent-space.md) | the hidden vector space where geometry encodes meaning  |
| GAN          | [`glossary/gan.md`](references/glossary/gan.md)                   | generator-vs-discriminator generative architecture      |
| Val loss     | [`glossary/val-loss.md`](references/glossary/val-loss.md)         | held-out validation error; the overfitting tripwire     |
| GPT          | [`glossary/gpt.md`](references/glossary/gpt.md)                   | generative pre-trained (decoder-only) transformer LLM   |
| Tensor       | [`glossary/tensor.md`](references/glossary/tensor.md)             | n-dimensional numeric array; the core ML data structure |
| Transformer  | [`glossary/transformer.md`](references/glossary/transformer.md)   | self-attention architecture behind modern LLMs          |

Entries cross-link related terms with `[[slug]]` (the filename without `.md`), so reading
one often points you at the next.

## Adding entries

1. New file in `references/glossary/`, named `kebab-case.md`.
2. Start with `# Term`, then one tight paragraph. Add a `**See also:**` line linking
   related entries with `[[slug]]`.
3. Add a row to the table here **and** in `SKILL.md`, and add the term to the `SKILL.md`
   frontmatter trigger list (the description names each term, so keep it in sync).

## Scripts

[`scripts/`](scripts/) exists but is intentionally empty — this is a reference skill, not
a tooling one. Runnable helpers (demos, format conversions) would live here if added.
