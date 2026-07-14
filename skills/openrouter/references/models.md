# OpenRouter — models, variants & provider routing

## Discovering models

```bash
# Everything, with context length and per-token pricing
curl -sS https://openrouter.ai/api/v1/models \
  | jq -r '.data[] | [.id, (.context_length|tostring), .pricing.prompt, .pricing.completion] | @tsv'

# Filter by provider/family
curl -sS https://openrouter.ai/api/v1/models \
  | jq -r '.data[].id' | grep '^anthropic/'

# Cheapest models that have ≥200K context, sorted by input price
curl -sS https://openrouter.ai/api/v1/models \
  | jq -r '.data[] | select((.context_length//0) >= 200000)
           | [(.pricing.prompt|tonumber), .id] | @tsv' | sort -n | head
```

Pricing fields are **per token in USD** (multiply by 1e6 for $/M). `pricing.prompt` = input, `pricing.completion` = output; some models also have `pricing.image`, `pricing.request`, `pricing.web_search`.

## Model ID format

`provider/model[:variant]`

- `~` prefix on an id (e.g. `~anthropic/claude-opus-latest`) marks a floating "latest" alias.
- Bare aliases (`deepseek/deepseek-chat`) track the newest checkpoint; pin a version (`deepseek/deepseek-chat-v3.1`) for reproducibility.

### Example IDs

- `anthropic/claude-opus-4.1`
- `openai/gpt-5`
- `google/gemini-2.5-pro`
- `deepseek/deepseek-chat`
- `meta-llama/llama-3.3-70b-instruct`
- `openrouter/auto` — let OpenRouter pick a model for the prompt

Browse and search the full list at https://openrouter.ai/models.

### Variant suffixes

| Suffix            | Meaning                                                         |
| ----------------- | --------------------------------------------------------------- |
| `:free`           | Free tier — heavily rate-limited, may queue/drop. Testing only. |
| `:nitro`          | Routes to highest-throughput provider (latency-optimized).      |
| `:floor`          | Routes to cheapest provider for the model.                      |
| `openrouter/auto` | Let OpenRouter choose a model for the prompt.                   |

## Provider routing

A single model is often served by multiple upstream providers at different price/latency/quality. Control selection with the `provider` object:

```jsonc
{
  "model": "meta-llama/llama-3.3-70b-instruct",
  "messages": [...],
  "provider": {
    "order": ["deepinfra", "together"],   // try these first, in order
    "allow_fallbacks": true,               // fall back to others if they fail (default true)
    "require_parameters": true,            // only providers supporting all your params
    "data_collection": "deny",             // exclude providers that train on data
    "sort": "throughput"                   // or "price" / "latency"
  }
}
```

Pin to one provider for deterministic behavior: `"provider": {"order": ["fireworks"], "allow_fallbacks": false}`.

## Model-level fallback

Independent of provider routing — try a list of _different models_ until one returns:

```jsonc
{
  "model": "openai/gpt-5",
  "models": ["openai/gpt-5", "anthropic/claude-sonnet-4.6", "deepseek/deepseek-chat"],
  "messages": [...]
}
```

The response's `.model` tells you which one actually served the request.

## Quick checks

```bash
# List all models with pricing and context length
curl -sS https://openrouter.ai/api/v1/models | jq '.data[] | {id, context_length, pricing}'

# Check remaining credit / usage on this key
curl -sS https://openrouter.ai/api/v1/credits \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq
```

## Inspecting a single model's endpoints

```bash
curl -sS https://openrouter.ai/api/v1/models/anthropic/claude-sonnet-4.6/endpoints \
  | jq '.data.endpoints[] | {provider: .provider_name, ctx: .context_length, pricing}'
```
