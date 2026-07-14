# Text & chat

Prefer `polli`. For multi-turn, tool use, or JSON-mode that you want to keep in code, drop down to the OpenAI SDK pointed at `/v1`.

## CLI (preferred)

### One-shot generation

```bash
polli gen text "summarize the theory of relativity in three sentences"
```

Reads stdin too:

```bash
cat notes.md | polli gen text --system "Summarize as bullet points." --output summary.md
```

Flags:

| Flag                      | Purpose                                            |
| ------------------------- | -------------------------------------------------- |
| `--model <name>`          | Text model (see list below; default is `openai`)   |
| `--system <msg>`          | System message                                     |
| `--temperature <n>`       | 0–2                                                |
| `--max-tokens <n>`        | Output cap                                         |
| `--top-p <n>`             | Nucleus sampling (0–1)                             |
| `--frequency-penalty <n>` | -2 to 2                                            |
| `--presence-penalty <n>`  | -2 to 2                                            |
| `--seed <n>`              | Reproducibility                                    |
| `--json-response`         | Force JSON object output                           |
| `--reasoning <effort>`    | `low` \| `medium` \| `high` (for reasoning models) |
| `--image <url>`           | Attach image(s) for vision models. Repeatable      |
| `--output <path>`         | Save to file instead of stdout                     |
| `--no-stream`             | Wait for the full response instead of streaming    |

### Interactive chat

```bash
polli gen chat --model openai-large
```

Multi-turn session in the terminal.

### Models

Free tier:

- `openai` — GPT-5.4 Nano, fast & balanced [tools]
- `openai-fast` — GPT-5 Nano, ultra fast & cheap [tools]
- `openai-large` — GPT-5.4, most powerful free [tools, reasoning]
- `qwen-coder` — Qwen3 Coder 30B [tools]
- `mistral` — Mistral Small 3.2 [tools]
- `openai-audio` / `openai-audio-large` — voice I/O
- `gemini-fast` — Gemini 2.5 Flash Lite [tools, search, code-exec]
- `gemini-search` — Gemini 2.5 Flash Lite Search [search]
- `deepseek` — DeepSeek V3.2 [tools, reasoning]
- `grok` — Grok 4.1 Fast [tools]
- `grok-large` — Grok 4.20 Reasoning [tools, reasoning]
- `midijourney` — AI music composition [tools]
- `claude-fast` — Claude Haiku 4.5 [tools]
- `perplexity-fast`, `perplexity-reasoning`
- `kimi` — Moonshot Kimi K2.5 [tools, reasoning]
- `nova-fast`, `nova` — Amazon Nova
- `glm` — Z.ai GLM-5.1 744B MoE [tools, reasoning]
- `minimax` — MiniMax M2.7 [tools, reasoning]
- `polly` — Pollinations assistant with GitHub/code-search/web tools (alpha)
- `qwen-coder-large`, `qwen-vision`, `qwen-safety`

Paid:

- `gemini` (Gemini 3 Flash), `gemini-flash-lite-3.1`, `gemini-large` (Gemini 3.1 Pro)
- `claude` (Sonnet 4.6), `claude-large` (Opus 4.6)
- `midijourney-large`
- `qwen-large`, `mistral-large`

### Examples

```bash
# JSON response
polli gen text "list 3 primary colors with hex codes" --json-response --model openai

# With reasoning effort
polli gen text "solve this logic puzzle: ..." --model grok-large --reasoning high

# Vision (describe an image)
polli gen text "describe this image" --model openai-large --image https://example.com/photo.jpg

# Piped summarization
curl -sS https://example.com/article.html | polli gen text --system "Summarize to 5 bullets." --output bullets.md
```

## HTTP API (fallback)

### GET `/text/{prompt}` — plain-text response

```bash
curl -sS --fail-with-body \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/text/What%20is%20AI?" -o answer.txt
```

Query params: `model`, `seed`, `system`, `json`, `temperature`, `stream`.

### POST `/v1/chat/completions` — OpenAI-compatible

Any OpenAI SDK:

```python
from openai import OpenAI
client = OpenAI(base_url="https://gen.pollinations.ai/v1", api_key=os.environ["POLLINATIONS_API_KEY"])
r = client.chat.completions.create(
    model="openai",
    messages=[
        {"role": "system", "content": "You are a terse poet."},
        {"role": "user",   "content": "Write a haiku about code."},
    ],
    temperature=0.8,
)
print(r.choices[0].message.content)
```

Body fields:

- `model` (default `"openai"`)
- `messages` (required): `[{role, content}]`
- `stream` (bool): SSE streaming
- `temperature` (0–2), `seed` (int, `-1` random)
- `response_format`: `{type: "json_object"}` forces JSON
- `tools` / `tool_choice`: standard OpenAI function-calling shape

### Vision input

```json
{
  "role": "user",
  "content": [
    { "type": "text", "text": "What's in this image?" },
    { "type": "image_url", "image_url": { "url": "https://example.com/x.jpg" } }
  ]
}
```

Base64: `"url": "data:image/jpeg;base64,<encoded>"`.

### Audio input (STT via chat)

```json
{
  "role": "user",
  "content": [
    { "type": "text", "text": "Transcribe this:" },
    {
      "type": "input_audio",
      "input_audio": { "data": "<base64>", "format": "wav" }
    }
  ]
}
```

Or use `POST /v1/audio/transcriptions` with multipart.
