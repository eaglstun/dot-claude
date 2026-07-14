# Pollinations.AI — full reference

Canonical source: <https://enter.pollinations.ai/api/docs/llm.txt>. A pristine snapshot is kept at `references/llm.txt` in this skill. Refetch if anything here looks stale.

## Base URLs

- Generation: `https://gen.pollinations.ai`
- Auth dashboard / API keys: `https://enter.pollinations.ai`
- Media storage: `https://media.pollinations.ai`

## Authentication

All generation requests require an API key. Model-listing endpoints are open.

| Method | Where           | Example                        |
| ------ | --------------- | ------------------------------ |
| Header | `Authorization` | `Authorization: Bearer sk_...` |
| Query  | `key`           | `?key=sk_...`                  |

Key types:

- `sk_...` — secret, server-side only. Full permissions.
- `pk_...` — publishable, safe to ship to clients. Rate-limited.

Treat keys as secrets. Read from env (`$POLLINATIONS_API_KEY`) or a gitignored file.

## Endpoints

### `POST /v1/chat/completions` — OpenAI-compatible chat

Works with any OpenAI SDK via `base_url="https://gen.pollinations.ai/v1"`.

Body:

- `model` (string, default `"openai"`)
- `messages` (array, required): `[{role: "user"|"assistant"|"system", content: "..."}]`
- `stream` (boolean, default false): SSE streaming
- `temperature` (number, 0.0–2.0)
- `seed` (integer, default 0; `-1` for random)
- `response_format` (`{type: "json_object"}`): force JSON output
- `tools` / `tool_choice`: standard OpenAI function-calling shape

### `GET /text/{prompt}` — simple text

Plain-text response. Query params: `model`, `seed`, `system`, `json`, `temperature`, `stream`.

### `GET /image/{prompt}` — image OR video (binary)

Returns `image/jpeg` or `video/mp4` depending on the model.

Shared params:

- `model` (string, default `"zimage"`)
- `width` (int, default 1024), `height` (int, default 1024)
- `seed` (int, default 0; `-1` random). Honored by `flux`, `zimage`, `seedream`, `klein`, `seedance`.
- `enhance` (bool, default false) — AI prompt enhancement
- `negative_prompt` (string) — `flux`, `zimage` only
- `safe` (bool, default false) — safety filter
- `quality` (`low`|`medium`|`high`|`hd`, default `medium`) — `gptimage`, `gptimage-large`
- `image` (string) — reference image URL(s), `|` or `,` separated
- `transparent` (bool, default false) — `gptimage`, `gptimage-large`
- `reasoning` (bool, default false) — enable thinking for text/layout; `nanobanana`, `nanobanana-2`, `nanobanana-pro`

Video-only params:

- `duration` (int, 1–10 seconds)
- `aspectRatio` (`"16:9"` or `"9:16"`)
- `audio` (bool, default false; `wan` always has audio)

### `POST /v1/images/generations` — OpenAI-compatible images

Body:

- `prompt` (string, required)
- `model` (string, default `"flux"`)
- `size` (string, default `"1024x1024"` — `WIDTHxHEIGHT`)
- `response_format` (`"url"` | `"b64_json"`, default `"b64_json"`)
- `quality`, `seed`, `nologo`, `enhance`, `safe` — same as GET

### `POST /v1/images/edits` — OpenAI-compatible edits

JSON or multipart. Body:

- `prompt` (string, required)
- `image` (string or array) — source URL(s), or multipart file field
- `model` (string, default `"flux"`)

### `GET /audio/{text}` — TTS or music

Returns `audio/mpeg`. Query: `voice`, `model` (`elevenlabs` | `elevenmusic` | `acestep`), `duration`.

### `POST /v1/audio/speech` — OpenAI-compat TTS

Body: `{input, voice, model}`.

### `POST /v1/audio/transcriptions` — STT

Multipart: `file` (audio), `model` (`whisper-large-v3` | `scribe`).

### `GET /v1/models` — list text models (OpenAI format, no auth)

### `GET /image/models` — list image/video models with metadata (no auth)

## Text models

Free tier:

- `openai` — GPT-5.4 Nano, fast & balanced [tools]
- `openai-fast` — GPT-5 Nano, ultra fast & affordable [tools]
- `openai-large` — GPT-5.4 [tools, reasoning]
- `openai-audio` — GPT Audio Mini, voice I/O [tools]
- `openai-audio-large` — GPT Audio 1.5, premium voice
- `qwen-coder` — Qwen3 Coder 30B [tools]
- `mistral` — Mistral Small 3.2 [tools]
- `gemini-fast` — Gemini 2.5 Flash Lite [tools, search, code-exec]
- `deepseek` — DeepSeek V3.2 [tools, reasoning]
- `grok` — Grok 4.1 Fast [tools]
- `grok-large` — Grok 4.20 Reasoning [tools, reasoning]
- `gemini-search` — Gemini 2.5 Flash Lite Search [search, code-exec]
- `midijourney` — AI music composition [tools]
- `claude-fast` — Claude Haiku 4.5 [tools]
- `perplexity-fast` — Perplexity Sonar [search]
- `perplexity-reasoning` — Perplexity Sonar Reasoning [reasoning, search]
- `kimi` — Moonshot Kimi K2.5 [tools, reasoning]
- `nova-fast`, `nova` — Amazon Nova [tools, reasoning (nova)]
- `glm` — Z.ai GLM-5.1 744B MoE [tools, reasoning]
- `minimax` — MiniMax M2.7 [tools, reasoning]
- `polly` — Pollinations assistant with GitHub/code-search/web tools [alpha]
- `qwen-coder-large`, `qwen-vision`, `qwen-safety`

Paid:

- `gemini` (Gemini 3 Flash), `gemini-flash-lite-3.1`, `gemini-large` (Gemini 3.1 Pro)
- `claude` (Sonnet 4.6), `claude-large` (Opus 4.6)
- `midijourney-large`
- `qwen-large` (Qwen3.6 Plus 396B MoE), `mistral-large`

## Image models

Free tier:

- `flux` — Flux Schnell, fast high-quality
- `zimage` — Z-Image Turbo, 6B Flux with 2x upscaling (default)
- `kontext` — FLUX.1 Kontext, in-context editing (image input)
- `klein` — FLUX.2 Klein 4B (image input)
- `gptimage` — GPT Image 1 Mini (image input)
- `gptimage-large` — GPT Image 1.5 (image input)
- `wan-image`, `qwen-image`

Paid:

- `nanobanana`, `nanobanana-2`, `nanobanana-pro` (Gemini image)
- `seedream5` (ByteDance ARK)
- `wan-image-pro` (4K, thinking mode)
- `grok-imagine`, `grok-imagine-pro`
- `p-image`, `p-image-edit`
- `nova-canvas` (Bedrock)

## Video models

Free tier:

- `ltx-2` — LTX-2.3, fast text-to-video with upscaler

Paid:

- `veo` — Google Veo 3.1 Fast (preview)
- `seedance` — Seedance Lite (BytePlus), better quality
- `seedance-pro` — Seedance Pro-Fast, better prompt adherence
- `wan` — Wan 2.6, text/image-to-video with audio, 2–15s, up to 1080p
- `wan-fast` — Wan 2.2, 5s, 480p
- `grok-video-pro` — xAI Grok Video Pro, 720p, 1–15s
- `p-video` — Pruna p-video, up to 1080p
- `nova-reel` — Amazon Bedrock Nova Reel, 6–60s, 720p

## Audio models

- `elevenlabs` — ElevenLabs v3 TTS, expressive voices with emotions & audio tags
- `elevenmusic` — ElevenLabs Music, studio-grade music from text
- `whisper` — Whisper Large V3 STT (OVH, alpha)
- `scribe` — ElevenLabs Scribe v2 STT, 90+ languages, diarization
- `acestep` — ACE-Step 1.5 Turbo, music with lyrics (alpha)

## Voices (TTS)

Core: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`, `ash`, `ballad`, `coral`, `sage`, `verse`.

ElevenLabs: `rachel`, `domi`, `bella`, `elli`, `charlotte`, `dorothy`, `sarah`, `emily`, `lily`, `matilda`, `adam`, `antoni`, `arnold`, `josh`, `sam`, `daniel`, `charlie`, `james`, `fin`, `callum`, `liam`, `george`, `brian`, `bill`.

## Vision input (chat)

Any vision-capable text model (e.g. `openai`, `openai-large`, `qwen-vision`). Content list:

```json
{
  "role": "user",
  "content": [
    { "type": "text", "text": "What's in this image?" },
    { "type": "image_url", "image_url": { "url": "https://example.com/x.jpg" } }
  ]
}
```

Base64 variant: `"url": "data:image/jpeg;base64,<encoded>"`.

## Audio input (STT via chat)

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

Or use the dedicated `POST /v1/audio/transcriptions` endpoint with a multipart file upload.

## Error codes

JSON error body: `{status, success: false, error: {code, message}}`.

- `400` — invalid parameters
- `401` — missing/invalid API key
- `402` — insufficient balance (chosen model is paid — switch to a free-tier model)
- `403` — permission denied (key lacks the right scope)
- `500` — server error

## Account endpoints

All require auth with the matching `account:<scope>` permission.

- `GET /api/account/profile` — name, email, tier, createdAt, nextResetAt (`account:profile`)
- `GET /api/account/balance` — remaining pollen (`account:balance`)
- `GET /api/account/usage` — per-request history; params `format`, `days`, `limit`, `before`
- `GET /api/account/usage/daily` — daily aggregates, max 90 days, cached 1h
- `GET /api/account/keys` — list keys (sk\_ only, `account:keys`)
- `POST /api/account/keys` — create a key (sk\_ only)
- `DELETE /api/account/keys/:id` — revoke a key
- `GET /api/account/key` — info about the current key

### Create-key body

```json
{
  "name": "display name",
  "type": "secret" | "publishable",
  "expiresIn": 604800,
  "allowedModels": ["flux", "openai"],
  "pollenBudget": 10,
  "accountPermissions": ["balance", "usage"]
}
```

Response returns the full key value exactly once — store it immediately.

## Media storage (`media.pollinations.ai`)

Content-addressed file storage for passing media between steps. Max 10 MB, 14-day TTL (re-upload resets it).

- `POST /upload` — multipart (`file`), raw binary, or JSON `{data (base64), contentType?, name?}`. Returns `{id, url, contentType, size, duplicate}`. Requires API key.
- `GET /{hash}` — retrieve (no auth, immutable cache)
- `HEAD /{hash}` — existence check

## Bring Your Own Pollen (BYOP) — end-user auth

Let your users pay for their own usage. Two flows, one consent screen.

### Web apps (redirect)

1. Send user to `https://enter.pollinations.ai/authorize?redirect_uri=<your_app_url>&client_id=<pk_yourkey>`. Optional query params: `scope`, `models`, `budget`, `expiry` (days), `state`.
2. User returns with `#api_key=sk_...` (or `#error=access_denied`) in the URL fragment.

### CLI / headless (device code)

```bash
# 1. request a device code
curl -X POST https://enter.pollinations.ai/api/device/code \
  -H 'Content-Type: application/json' \
  -d '{"client_id": "pk_yourkey", "scope": "generate"}'
# → {device_code, user_code: "ABCD-1234", verification_uri: "/device"}

# 2. user enters ABCD-1234 at enter.pollinations.ai/device

# 3. poll every ~5s
curl -X POST https://enter.pollinations.ai/api/device/token \
  -H 'Content-Type: application/json' \
  -d '{"device_code": "..."}'
# pending: {"error": "authorization_pending"}
# done:    {"access_token": "sk_...", "token_type": "bearer", "scope": "generate"}
```

### Userinfo (OIDC shape)

```bash
curl https://enter.pollinations.ai/api/device/userinfo \
  -H 'Authorization: Bearer sk_...'
# → {sub, name, preferred_username, email, picture}
```

Keys expire in 30 days by default and are revocable from the dashboard.

## Clients / SDKs

- **CLI:** `npx @pollinations_ai/cli` (binary `polli`) — `polli gen image|video|text|audio`, structured `--json` output, stdin piping.
- **OpenAI SDK:** any — set `base_url="https://gen.pollinations.ai/v1"` and pass your Pollinations key.
- **React hooks:** `@pollinations/react` — `usePollinationsImage`, `usePollinationsText`, `usePollinationsChat`.
- **Python:** `pollinations_ai`, `pypollinations`.
- **MCP server:** available for direct LLM-driven generation.
