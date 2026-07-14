---
name: openrouter
version: 1.0.0
public: true
description: >-
  Direct calls to OpenRouter's OpenAI-compatible API for chat/text completions across
  hundreds of models from one key — OpenAI, Anthropic, Google, Meta, DeepSeek, Mistral,
  Qwen, and more. Use for raw LLM output (drafting, classification, translation, fast
  chat) when you want one endpoint, automatic provider fallback, or a model not available
  through other skills.
semantic_id: "IG2DMNG5pVX7shlyN68mrTVpZ3riUAAP"
related_ids:
  - "KGVGsr_7sxHB-AhzVBwGrTRxpdj3wAAF"
  - "TGvkGBO_HxdJfBFmE53XyTdEp2jkQAAI"
topic_id: "v2:DLDH"
topic_path: "model-runners/ai-aggregators"
---

# OpenRouter Skill

Direct calls to OpenRouter, a single OpenAI-compatible gateway that routes to hundreds of models across providers. One API key, one endpoint, unified billing.

- **Base URL:** `https://openrouter.ai/api/v1`
- **API key:** `OPENROUTER_API_KEY`.
  - **Mac:** stored in this skill's `.env` (next to `SKILL.md`, perms `600`). Load it before a call: `set -a; . "$(dirname SKILL.md)/.env"; set +a` — or from the skill dir, `set -a; . ./.env; set +a`.
  - **Pi 5:** set in `~/.openrouter.env` (sourced by both `~/.profile` and `~/.bashrc`) — already in the login shell, no manual load needed.
  - Get a new key at https://openrouter.ai/keys.
- **Wire format:** identical to the OpenAI Chat Completions API — any OpenAI SDK works by pointing `base_url` at the URL above.
- **Model IDs:** namespaced `provider/model`, optionally with a variant suffix (`:free`, `:nitro`, `:floor`); `openrouter/auto` lets OpenRouter pick. Example IDs, pricing queries, and routing controls live in `references/models.md`.

> **Billing note:** OpenRouter is pay-as-you-go from a prepaid credit balance. Calls return `402` / `Insufficient credits` when the balance is empty — top up at https://openrouter.ai/settings/credits.

## Quick start — chat completion

```bash
curl -sS https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-chat",
    "messages": [{"role": "user", "content": "Say hi in one word."}]
  }' | jq -r '.choices[0].message.content'
```

Optional ranking headers (used for OpenRouter's public app leaderboard; harmless to omit):
`-H "HTTP-Referer: <your-site>"` and `-H "X-Title: <app-name>"`.

## References - load on demand

Each is self-contained. If unsure, default to `references/chat.md`.

- **`references/chat.md`** - full chat-completions reference: model picker table with live prices, common + OpenRouter-specific request fields, Python SDK usage, streaming, cost/usage tracking. _Read when making any text or chat completion beyond the quick start above._
- **`references/models.md`** - discovering models via the API, example IDs, variant suffixes, provider routing and model-level fallback, credit checks. _Read when picking a model, checking pricing, or pinning/ordering providers._
- **`references/tool-calling.md`** - tool / function calling and strict JSON structured outputs. _Read when the call needs tools or schema-enforced JSON._
- **`references/vision.md`** - image inputs for vision-capable chat models. _Read when describing or analyzing an image._

## Gotchas

- **Pricing varies by model and provider** — check `pricing` from the `/models` endpoint before high-volume calls. Prices are per token (USD).
- **Not every model supports every feature.** Tool calling, structured outputs, and vision depend on the upstream model; check the model's page on openrouter.ai/models.
- **`:free` models are heavily rate-limited** and may queue or drop — fine for testing, not for throughput.
- **Provider routing is automatic** by default; if you need deterministic behavior, use the `provider` field to pin one upstream (`references/models.md`).

## Account

- Keys: https://openrouter.ai/keys
- Credits / billing: https://openrouter.ai/settings/credits
- Activity log: https://openrouter.ai/activity
- Docs: https://openrouter.ai/docs

## When NOT to use this

If your assigned model already handles the task, just use it. Reach for OpenRouter when you genuinely need a different model, broad provider coverage from one key, or automatic fallback across providers.
