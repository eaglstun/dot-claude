# Together — text completions (legacy, non-chat)

> **Script:** `scripts/completions.py "prompt" [--model --max-tokens --stop]` wraps this endpoint.

The raw completion endpoint — takes a `prompt` string instead of a `messages` array, and returns text at `choices[0].text` (note: `.text`, **not** `.message.content`). **Prefer `chat.md` for almost everything;** reach for this only for base/completion models, raw-prompt control, or porting old completion-style code.

Endpoint: `POST https://api.together.ai/v1/completions`

```bash
curl -sS https://api.together.ai/v1/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "prompt": "The largest city in France is",
    "max_tokens": 8,
    "temperature": 0
  }' | jq -r '.choices[0].text'
```

Response object is `"text.completion"`; the text is at `.choices[0].text`, with `usage` and `finish_reason` alongside.

## Parameters

| Field                | Notes                                                |
| -------------------- | ---------------------------------------------------- |
| `model`              | **Required.** Same serverless catalog as chat        |
| `prompt`             | **Required.** Raw text to complete                   |
| `max_tokens`         | Cap completion length                                |
| `temperature`        | 0–1 randomness                                       |
| `top_p` / `top_k`    | Nucleus / top-k sampling                             |
| `stop`               | Array of stop strings                                |
| `repetition_penalty` | Discourage repetition                                |
| `stream`             | `true` for SSE streaming (same parsing as `chat.md`) |
| `logprobs`           | Return top-k token logprobs (0–20)                   |
| `echo`               | Include the prompt in the response                   |
| `n`                  | Number of completions (1–128)                        |

## vs. chat/completions

`chat/completions` takes `messages` (roles + content) and returns `.choices[0].message.content`; this takes a flat `prompt` and returns `.choices[0].text`. Instruction-tuned models are trained for the chat format — for those, use `chat.md`. This endpoint shines with base models and when you want exact control over the raw prompt string (few-shot templates, fill-in patterns, logprob/`echo` tricks).
