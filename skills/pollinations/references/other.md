# Other — auth, keys, usage, uploads, BYOP, errors

For gen-by-medium docs, see `image.md`, `video.md`, `audio.md`, `text.md`. This file covers everything else.

## Auth

All generation requests require an API key. Model-listing endpoints are open.

```bash
# Header
Authorization: Bearer $POLLINATIONS_API_KEY
# Or query param
?key=$POLLINATIONS_API_KEY
```

Key types:

- `sk_...` — secret, server-side only. Full permissions.
- `pk_...` — publishable, safe to ship to clients. Rate-limited.

Get a key at <https://enter.pollinations.ai>. Read from env or a gitignored file — never hardcode. If `$POLLINATIONS_API_KEY` isn't set, tell the user so they can export it before proceeding.

### CLI auth

```bash
polli auth login      # OAuth device flow, stores key locally
polli auth status     # current user + balance
polli auth logout     # clear stored key
polli --key sk_...    # override stored key for one command
```

## Listing models

```bash
polli models                 # all
polli models --type image    # image only
polli models --type video    # video only
polli models --type audio    # audio (includes voice lists)
polli models --type text     # text
polli models --stats         # health / error rates
polli models --json          # machine-readable
```

HTTP:

- `GET /v1/models` — text models (OpenAI format)
- `GET /image/models` — image/video models with metadata

No auth needed for either.

## Usage & balance

```bash
polli usage              # current pollen balance
polli usage --history    # per-request history (default last 20)
polli usage --daily      # daily aggregate
polli usage --limit 100  # more records
```

HTTP endpoints (need matching `account:<scope>` permission):

- `GET /api/account/profile` — name, email, tier, createdAt, nextResetAt
- `GET /api/account/balance` — remaining pollen
- `GET /api/account/usage` — per-request history. Params: `format` (json|csv), `days` (1–90, default 30), `limit` (1–50000, default 100), `before` (ISO cursor)
- `GET /api/account/usage/daily` — daily aggregates, max 90 days, cached 1h

## API keys

```bash
polli keys list                               # all keys
polli keys info                               # current key details
polli keys create --name "my-bot" --type secret
polli keys revoke <id>
```

HTTP (requires `sk_` key with `account:keys`):

- `GET /api/account/keys` — list
- `POST /api/account/keys` — create
- `DELETE /api/account/keys/:id` — revoke
- `GET /api/account/key` — info about the current key

Create-key body:

```json
{
  "name": "display name",
  "type": "secret",
  "expiresIn": 604800,
  "allowedModels": ["flux", "openai"],
  "pollenBudget": 10,
  "accountPermissions": ["balance", "usage"]
}
```

Response returns the full key value exactly once — store it immediately.

## Media storage (`media.pollinations.ai`)

Content-addressed storage for passing media between steps. Max 10 MB, 14-day TTL (re-upload resets it).

```bash
polli upload ./frame.png
# → https://media.pollinations.ai/<16-char-hex>
```

HTTP:

- `POST https://media.pollinations.ai/upload` — multipart (`file`), raw binary, or JSON `{data (base64), contentType?, name?}`. Returns `{id, url, contentType, size, duplicate}`. Requires API key.
- `GET /{hash}` — retrieve (no auth, immutable cache)
- `HEAD /{hash}` — existence check

Useful for chaining: generate an image → upload → pass its URL as `--image` to a video model.

## Bring Your Own Pollen (BYOP) — end-user auth

Lets your users pay for their own usage. Two flows, one consent screen.

### Web apps (redirect)

1. Send user to `https://enter.pollinations.ai/authorize?redirect_uri=<your_app_url>&client_id=<pk_yourkey>`. Optional params: `scope`, `models`, `budget`, `expiry` (days), `state`.
2. User returns with `#api_key=sk_...` (or `#error=access_denied`) in the URL fragment. Fragments never hit server logs.

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

### OIDC userinfo

```bash
curl https://enter.pollinations.ai/api/device/userinfo \
  -H 'Authorization: Bearer sk_...'
# → {sub, name, preferred_username, email, picture}
```

Keys expire in 30 days by default and are revocable from the dashboard.

## Errors

JSON body shape: `{status, success: false, error: {code, message}}`.

| Code | Meaning                 | Fix                                                                        |
| ---- | ----------------------- | -------------------------------------------------------------------------- |
| 400  | Invalid parameters      | Check param names/values                                                   |
| 401  | Missing/invalid API key | Set `$POLLINATIONS_API_KEY` or run `polli auth login`                      |
| 402  | Insufficient balance    | Chosen model is paid — retry with a free-tier model (see per-medium lists) |
| 403  | Permission denied       | Key lacks the scope — create one with the right `accountPermissions`       |
| 500  | Server error            | Retry; if persistent, check status                                         |

## Clients / SDKs

- **CLI:** `npx @pollinations_ai/cli` or global install — binary `polli`. Structured `--json` output, stdin piping, friendly 402 hints.
- **OpenAI SDK (any language):** set `base_url="https://gen.pollinations.ai/v1"` and pass your key.
- **React hooks:** `@pollinations/react` — `usePollinationsImage`, `usePollinationsText`, `usePollinationsChat`.
- **Python:** `pollinations_ai`, `pypollinations`.
- **MCP server:** available for direct LLM-driven generation.

## Canonical API doc

The pristine upstream doc lives at `references/llm.txt` in this skill. Refetch from <https://enter.pollinations.ai/api/docs/llm.txt> if anything here looks stale.
