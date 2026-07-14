# Together — model selection & the serverless gotcha

## Default chat model

**`deepseek-ai/DeepSeek-V3.1`** — use it unless you have a specific reason to pick another. Full per-model guide and register notes are in `references/chat.md`.

## Serverless vs dedicated — the big gotcha

Together lists hundreds of models but only some are callable from a standard key. Models listed at $0/M tokens almost always require paid **dedicated endpoints** and return `model_not_available` / `non-serverless` from the serverless API. **Before adding any new model to a fallback chain, test it:**

```bash
curl -sS https://api.together.ai/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<model-id>","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  | grep -E '"choices"|"non-serverless"'
```

`"choices"` in the response = serverless, safe to use. `"non-serverless"` in an error = dedicated only, skip it.
