#!/usr/bin/env bash
# PostToolUse hook — align/format markdown with prettier after Write/Edit/MultiEdit.
#
# Reads the tool-event JSON on stdin, extracts the edited file path, and if it is a
# .md/.markdown file, runs `prettier --write` on it (prettier defaults to
# proseWrap:preserve, so prose isn't rewrapped — mainly tables get aligned).
# Always exits 0 so it can never block or fail an edit.
set -u

input="$(cat)"
file="$(printf '%s' "$input" | python3 -c 'import sys, json
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("file_path", "") or "")
except Exception:
    print("")' 2>/dev/null)"

case "$file" in
  *.md | *.markdown) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

# Locate prettier: PATH first, then fall back to loading nvm for its global bin.
pretty="$(command -v prettier 2>/dev/null || true)"
if [ -z "$pretty" ]; then
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1091
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" >/dev/null 2>&1
  pretty="$(command -v prettier 2>/dev/null || true)"
fi

[ -n "$pretty" ] && "$pretty" --write "$file" >/dev/null 2>&1
exit 0
