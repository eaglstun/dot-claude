# Together — chat completions

> **Script:** `scripts/chat.py "prompt" [--model --system --json --messages-file]` wraps this endpoint.

Endpoint: `POST https://api.together.ai/v1/chat/completions` (OpenAI-compatible).

```bash
curl -sS https://api.together.ai/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-V3.1",
    "messages": [{"role":"user","content":"your prompt here"}],
    "max_tokens": 2048,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'
```

Response shape: `.choices[0].message.content`.

## Serverless models (verified callable)

| Model                                     | $/M in | $/M out | ctx  | Notes                                                                                                                                                 |
| ----------------------------------------- | ------ | ------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `deepseek-ai/DeepSeek-V3.1`               | $0.60  | $1.70   | 128K | **Default pick.** Philosophical/reflective register, engages with introspection well; brief "I'm just an AI" disclaimers manageable via system prompt |
| `openai/gpt-oss-120b`                     | $0.15  | $0.60   | 128K | Fallback #1 — cheap but reaches for emoji headers, tables, "TL;DR" scaffolding even on conversational prompts                                         |
| `meta-llama/Llama-3.3-70B-Instruct-Turbo` | $0.88  | $0.88   | 128K | Fallback #2 — smooth-robot RLHF voice, reliable for tool calls                                                                                        |
| `deepcogito/cogito-v2-1-671b`             | $1.25  | $1.25   | 160K | Cleaner default register than gpt-oss (no emoji/tables) but less distinctive than DeepSeek — competent but not philosophical                          |
| `deepseek-ai/DeepSeek-R1`                 | $3.00  | $7.00   | 160K | Full reasoning model; slow but deep — use for hard analysis only                                                                                      |
| `openai/gpt-oss-20b`                      | $0.05  | $0.20   | 128K | Cheaper sibling but returns empty completions sometimes — flaky                                                                                       |
| `Qwen/Qwen2.5-7B-Instruct-Turbo`          | $0.30  | $0.30   | 32K  | Cheap small model for quick tasks                                                                                                                     |
| `deepseek-ai/DeepSeek-V3`                 | broken | —       | —    | Returns multilingual gibberish on Together — do not use                                                                                               |

## Register notes

If you care about a distinctive, terse, conversational voice (not just task completion), model choice matters more than the price column suggests:

- **`DeepSeek V3.1`** — philosophical/reflective register; lets a system-prompt persona carry through instead of flattening it. Best voice of the serverless set.
- **`gpt-oss-120b`** — cheap, but RLHF'd to feel "comprehensive": reaches for emoji-numbered headers (1️⃣ 2️⃣), unprompted tables/checklists, and "### TL;DR" even on one-line conversational prompts. Fine for structured output, fights a terse persona.
- **`cogito-v2-1-671b`** — cleaner default register than gpt-oss (no emoji/tables) but reads more "competent" than "distinctive."
- **`Llama 3.3 70B`** — smooth-robot voice, but a reliable tool-calling fallback.

## Common parameters

- `temperature` (0–2, default 0.7) — lower = more deterministic
- `top_p` (0–1) — nucleus sampling
- `max_tokens` — cap completion length
- `stop` — array of stop strings
- `response_format: {"type":"json_object"}` — JSON-only output
- `tools` — function-calling array (works on Llama 3.3, DeepSeek V3.1, Qwen Instruct)

## Streaming

Add `"stream": true` and parse SSE:

```bash
curl -N https://api.together.ai/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-ai/DeepSeek-V3.1","messages":[{"role":"user","content":"..."}],"stream":true}'
```

## Listing all models

```bash
curl -sS https://api.together.ai/v1/models -H "Authorization: Bearer $TOGETHER_API_KEY" \
  | jq '.[] | {id, ctx: .context_length, in: .pricing.input, out: .pricing.output}'
```

Remember: a non-zero price doesn't guarantee serverless, and a zero price almost always means dedicated-only. Test before relying on it (snippet in `references/serverless.md`).

## Models that look free but aren't accessible

Together lists many models at $0/M (`Hermes-2-Mixtral`, `Mistral-Small-24B`, `Llama-4-Scout`, `Qwen3-Next-80B`, `MiniMax-M2`, `Mixtral-8x22B`, `Cogito-v1-preview-*`, `NVIDIA-Nemotron-Nano-9B-v2`). These require **paid dedicated endpoints** to call. Don't add them to fallback chains — they fail with `model_not_available` from serverless requests.

## Cost reference

The `$5` initial credit covers ~5.7M Llama-3.3-70B input tokens, or ~8.3M DeepSeek V3.1 input tokens.
