# openrouter

Claude Code skill for direct calls to the **OpenRouter** OpenAI-compatible API (`https://openrouter.ai/api/v1`) — one key, one endpoint, hundreds of models across OpenAI, Anthropic, Google, Meta, DeepSeek, Mistral, Qwen, xAI and more. Use it for raw LLM output (drafting, classification, translation, fast chat) when you want broad model coverage or automatic provider/model fallback.

## Setup

Set `OPENROUTER_API_KEY`:

- **Mac:** stored in this skill's `.env` (next to `SKILL.md`, perms `600`). Load before a call: `set -a; . ./.env; set +a` from the skill dir.
- **Pi 5:** in `~/.openrouter.env`, sourced by `~/.profile` and `~/.bashrc` — already in the login shell.

Get a key at <https://openrouter.ai/keys>; check credits at <https://openrouter.ai/settings/credits>. Calls return `402` / `Insufficient credits` with no balance.

## Usage

`SKILL.md` is the entry point; Claude loads the reference matching the task:

| Task                                    | Reference                                                  |
| --------------------------------------- | ---------------------------------------------------------- |
| Chat / text completions (default)       | [`references/chat.md`](references/chat.md)                 |
| Find models, pricing, variants, routing | [`references/models.md`](references/models.md)             |
| Tool calling & structured JSON outputs  | [`references/tool-calling.md`](references/tool-calling.md) |
| Vision (analyze an image)               | [`references/vision.md`](references/vision.md)             |

Default chat model: **`deepseek/deepseek-chat`** (cheap, strong general model). Model IDs are `provider/model[:variant]` — `:free` (rate-limited), `:nitro` (fastest provider), `:floor` (cheapest), or `openrouter/auto`. Wire format is identical to OpenAI Chat Completions, so any OpenAI SDK works by pointing `base_url` at the URL above.

> Slugs and pricing drift — re-list with `/api/v1/models` to confirm before relying on a model.
