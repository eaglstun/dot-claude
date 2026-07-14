# OpenRouter — chat completions

Endpoint: `POST https://openrouter.ai/api/v1/chat/completions` (OpenAI-compatible).

```bash
curl -sS https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-chat",
    "messages": [{"role":"user","content":"your prompt here"}],
    "max_tokens": 2048,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'
```

Response shape: `.choices[0].message.content`. The actual model that served the request comes back in `.model` (useful when you used an alias or `:floor`/`auto` routing).

## Model picker (verified live 2026-05-30, prices $/M tokens)

| Model                                | $/M in | $/M out | ctx   | Notes                                                            |
| ------------------------------------ | ------ | ------- | ----- | ---------------------------------------------------------------- |
| `deepseek/deepseek-chat`             | $0.21  | $0.79   | 164K  | **Cheap default.** Alias → latest deepseek-chat; great $/quality |
| `deepseek/deepseek-v3.2`             | $0.25  | $0.38   | 131K  | Even cheaper, strong general model                               |
| `google/gemini-2.5-flash-lite`       | $0.10  | $0.40   | 1.05M | Cheapest big-context; fast; good for bulk/classification         |
| `qwen/qwen3-235b-a22b-thinking-2507` | $0.10  | $0.10   | 262K  | Flat-rate reasoning model, absurdly cheap                        |
| `openai/gpt-5-mini`                  | $0.25  | $2.00   | 400K  | Cheap OpenAI tier                                                |
| `openai/gpt-5`                       | $1.25  | $10.00  | 400K  | OpenAI flagship                                                  |
| `anthropic/claude-haiku-4.5`         | $1.00  | $5.00   | 200K  | Fast Claude                                                      |
| `anthropic/claude-sonnet-4.6`        | $3.00  | $15.00  | 1M    | Balanced Claude flagship                                         |
| `anthropic/claude-opus-4.8`          | $5.00  | $25.00  | 1M    | Top Claude; deep reasoning/coding                                |
| `x-ai/grok-4.20`                     | $1.25  | $2.50   | 2M    | Largest context here (2M)                                        |
| `mistralai/mistral-large-2512`       | $0.50  | $1.50   | 262K  | Cheap European flagship                                          |

Default to **`deepseek/deepseek-chat`** for one-off prompts unless you need a specific capability. Slugs and prices drift — re-list to confirm (see `models.md`).

> Pin a version (e.g. `deepseek/deepseek-chat-v3.1`) for reproducibility; the bare alias tracks the latest and may change which checkpoint serves you.

## Common parameters

- `temperature` (0–2, default 1.0) — lower = more deterministic
- `top_p`, `top_k`, `frequency_penalty`, `presence_penalty`, `repetition_penalty`
- `max_tokens` — cap completion length
- `stop` — array of stop strings
- `seed` — best-effort determinism (provider-dependent)
- `response_format: {"type":"json_object"}` — JSON-only output (see `tool-calling.md` for strict schemas)
- `tools` / `tool_choice` — function calling (see `tool-calling.md`)
- `usage: {"include": true}` — return token counts + cost in the response

## OpenRouter-specific fields

- `models: ["a/b","c/d"]` — ordered fallback list; tries each until one succeeds.
- `provider: {...}` — pin/rank upstream providers, control routing (see `models.md`).
- `transforms: ["middle-out"]` — auto-compress prompts that exceed the context window.

## Python (OpenAI SDK)

The wire format is identical to the OpenAI Chat Completions API, so any OpenAI SDK works by pointing `base_url` at OpenRouter:

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
resp = client.chat.completions.create(
    model="deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Say hi in one word."}],
)
print(resp.choices[0].message.content)
```

## Streaming

Add `"stream": true` and parse SSE (`data:` lines, terminated by `data: [DONE]`):

```bash
curl -N https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek/deepseek-chat","messages":[{"role":"user","content":"..."}],"stream":true}'
```

## Cost & usage

Append `"usage": {"include": true}` to get `.usage` with `prompt_tokens`, `completion_tokens`, and `cost` (USD) in the response. Or check the running balance any time:

```bash
curl -sS https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq
```
