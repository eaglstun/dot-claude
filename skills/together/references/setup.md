# Together — setup & environment

## API key

Read from the `TOGETHER_API_KEY` environment variable (never hardcoded or committed).

- **macOS/Linux:** `export TOGETHER_API_KEY=...` in `~/.zshenv`, `~/.bashrc`, or `~/.profile`
- **Windows PowerShell:** `setx TOGETHER_API_KEY "..."`, then reopen the shell

Base URL: `https://api.together.ai/v1` (video generation uses `/v2`).

## Billing

Calls return `Credit limit exceeded` if the account has no credits. Top up / check usage: <https://api.together.ai/settings/billing>.

## Tool dependencies

The reference `curl` examples use `curl`, `jq`, and `grep`; media provenance uses `exiftool` (images/video) and `ffmpeg` (audio). These are standard on macOS/Linux. On Windows, run them under WSL or Git Bash, or install the equivalents first (`brew install exiftool` if missing).

The `scripts/` helpers, by contrast, are **pure Python standard library** — no `jq`/`curl` needed, just Python 3.8+. (They still shell out to `exiftool`/`ffmpeg` for provenance, and skip it with a warning if those aren't installed.)
