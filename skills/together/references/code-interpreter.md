# Together — code interpreter (TCI)

> **Script:** `scripts/tci.py "code" [--session-id --upload f]` wraps this endpoint.

Together Code Interpreter (TCI) runs code in a hosted sandbox and returns the captured output — stdout, stderr, return values, and rendered artifacts (plots, HTML). Use it when you want a model's code to actually _run_ rather than just be emitted as text, or to do quick compute/data work against an uploaded file.

- Execute: `POST https://api.together.ai/v1/tci/execute`
- List sessions: `GET https://api.together.ai/v1/tci/sessions`

> **Language:** Python only (the `language` enum currently accepts `"python"`).

## Execute

```bash
curl -sS https://api.together.ai/v1/tci/execute \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "code": "import numpy as np\nprint(np.array([1,2,3]).sum())"
  }' | jq '.data.outputs'
```

Response wraps everything in `.data` (with a sibling `.errors`):

```json
{
  "data": {
    "session_id": "ses_abc123",
    "status": "success",
    "outputs": [{ "type": "stdout", "data": "6\n" }]
  },
  "errors": null
}
```

On failure, `.data` is `null` and `.errors` holds the problem:

```json
{ "data": null, "errors": ["<description or error object>"] }
```

## Request body

| Field        | Type   | Required | Notes                                                             |
| ------------ | ------ | -------- | ----------------------------------------------------------------- |
| `language`   | string | yes      | `"python"` (only value currently supported)                       |
| `code`       | string | yes      | The snippet to run                                                |
| `session_id` | string | no       | Reuse an existing session (see below). Omit to start a fresh one. |
| `files`      | array  | no       | Files to drop into the sandbox before the code runs (see below)   |

### Uploading files

Each entry in `files` is `{ "name", "encoding", "content" }`:

- `name` — filename as it appears in the sandbox working dir
- `encoding` — `"string"` for text, `"base64"` for binary
- `content` — the file data (raw text, or base64 for binary)

```json
"files": [
  { "name": "data.csv", "encoding": "string", "content": "a,b\n1,2\n3,4\n" }
]
```

Then read it in your `code` as a normal local file (`open("data.csv")`, `pd.read_csv("data.csv")`, …).

## Output types

`.data.outputs` is an ordered array; each item has a `type` and `data`:

| `type`           | Meaning                   | `data` shape                                               |
| ---------------- | ------------------------- | ---------------------------------------------------------- |
| `stdout`         | Standard output           | string                                                     |
| `stderr`         | Standard error stream     | string                                                     |
| `error`          | Exception / runtime error | string                                                     |
| `execute_result` | The cell's return value   | MIME object (`text/plain`, `application/json`, …)          |
| `display_data`   | Rendered visualization    | MIME object (`image/png`, `image/svg+xml`, `text/html`, …) |

**Saving a generated plot:** matplotlib/PIL output arrives as a `display_data` item with an `image/png` (base64) payload — decode and write it to disk yourself. If you persist it as a file, apply the **provenance rule** in `references/provenance.md` (embed model/prompt via `exiftool`).

## Stateful sessions

Omitting `session_id` starts a fresh sandbox and the response tells you the new id in `.data.session_id`. Pass that id back on the next call to reuse the **same kernel** — imports, variables, installed packages, and uploaded files all persist:

```bash
# 1) first call — capture the session id
SID=$(curl -sS https://api.together.ai/v1/tci/execute \
  -H "Authorization: Bearer $TOGETHER_API_KEY" -H "Content-Type: application/json" \
  -d '{"language":"python","code":"x = 41"}' | jq -r '.data.session_id')

# 2) reuse it — x is still defined
curl -sS https://api.together.ai/v1/tci/execute \
  -H "Authorization: Bearer $TOGETHER_API_KEY" -H "Content-Type: application/json" \
  -d "{\"language\":\"python\",\"code\":\"print(x + 1)\",\"session_id\":\"$SID\"}" \
  | jq -r '.data.outputs[].data'
```

Sessions are caller-scoped (you can't touch another account's session) and expire after a TTL — an expired or unknown `session_id` comes back as an error, so be ready to start a new one.

## List sessions

```bash
curl -sS https://api.together.ai/v1/tci/sessions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" | jq '.data.sessions'
```

Each session reports `id`, `execute_count`, and ISO-8601 `started_at` / `last_execute_at` / `expires_at`:

```json
{
  "data": {
    "sessions": [
      {
        "id": "ses_abc123",
        "execute_count": 5,
        "started_at": "2024-01-15T10:30:00Z",
        "last_execute_at": "2024-01-15T10:45:30Z",
        "expires_at": "2024-01-22T10:30:00Z"
      }
    ]
  },
  "errors": []
}
```

## Notes

- Base path is `/v1/tci/...` — same host and auth as the rest of the API.
- Python-only for now; no `language` value other than `"python"`.
- Pricing isn't published on the endpoint reference — check the Together pricing page / dashboard before leaning on it heavily.
