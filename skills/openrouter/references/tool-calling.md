# OpenRouter — tool calling & structured outputs

Both use the standard OpenAI wire format. Support is **per-model** — check the model page or filter `/models` by `supported_parameters`:

```bash
curl -sS https://openrouter.ai/api/v1/models \
  | jq -r '.data[] | select(.supported_parameters|index("tools")) | .id' | head
```

## Tool calling

```bash
curl -sS https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-chat",
    "messages": [{"role":"user","content":"What is the weather in Paris?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {"city": {"type":"string"}},
          "required": ["city"]
        }
      }
    }],
    "tool_choice": "auto"
  }'
```

The model replies with `.choices[0].message.tool_calls[]` (each has `.id`, `.function.name`, `.function.arguments` as a JSON string). The loop:

1. Send messages + `tools`.
2. If `tool_calls` come back, run each function locally.
3. Append the assistant message, then one `{"role":"tool","tool_call_id":"...","content":"<result>"}` per call.
4. Send again to get the final natural-language answer.

`tool_choice` accepts `"auto"`, `"none"`, `"required"`, or `{"type":"function","function":{"name":"get_weather"}}` to force a specific tool.

## Structured outputs (strict JSON schema)

For models advertising `structured_outputs` support, use `response_format` with `strict: true` — the output is guaranteed to validate against the schema:

```jsonc
{
  "model": "openai/gpt-5-mini",
  "messages": [
    { "role": "user", "content": "Extract: Ada Lovelace, born 1815, London." },
  ],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "person",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "born": { "type": "integer" },
          "city": { "type": "string" },
        },
        "required": ["name", "born", "city"],
        "additionalProperties": false,
      },
    },
  },
}
```

For models without strict-schema support, fall back to `"response_format": {"type":"json_object"}` and describe the shape in the prompt (validate the result yourself — it's best-effort, not guaranteed).
