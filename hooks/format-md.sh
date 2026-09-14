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

# ---------------------------------------------------------------------------
# VERBATIM GUARD (added 2026-08-03)
#
# Prettier is desirable almost everywhere — it aligns tables, which is the whole
# reason this hook exists. But on files that hold VERBATIM primary-source text
# (emails, message transcripts, or preserved evidence) it
# silently rewrites content. Measured against prettier 3.8.3 on 2026-08-03:
#
#   "Subject: Re:  budget  stuff"   ->  "Subject: Re: budget stuff"    (double spaces collapsed)
#   "Body with  double  spaces."    ->  "Body with double spaces."     (collapsed in prose too)
#   a bare ">" quote line           ->  DELETED                        (empty blockquote dropped)
#   "*emph*"                        ->  "_emph_"                       (emphasis normalized)
#   "__bold__"                      ->  "**bold**"                     (strong normalized)
#
# None of these are configurable — markdown treats internal whitespace and empty
# blockquote lines as insignificant, and prettier does not expose an emphasis
# marker option. So the only real fix is to not run it on those paths.
#
# In an archive used as an evidentiary record, a silently "corrected" quotation is
# worse than an ugly one. Skip these; format everything else.
#
# To add a path: append a pattern to VERBATIM_DENY. To carve one back in (e.g. an
# analysis subfolder that lives under a verbatim tree), append to VERBATIM_ALLOW —
# allow wins over deny.
# ---------------------------------------------------------------------------

VERBATIM_ALLOW='/transcripts/summaries/|/emails/summaries/|/texts/summaries/'
VERBATIM_DENY='/your/verbatim/paths/here/'

if ! printf '%s' "$file" | grep -qE "$VERBATIM_ALLOW"; then
  if printf '%s' "$file" | grep -qE "$VERBATIM_DENY"; then
    echo "format-md: skipped $file — verbatim path (prettier would rewrite quoted text)."
    exit 0
  fi
fi

# Never format a file with unresolved merge-conflict markers. Prettier does not
# recognize them as markers: it reads `=======` as a setext H1 underline (promoting
# the line above it to a heading) and `>>>>>>> branch` as seven nested blockquotes,
# destroying the markers while leaving the content — so the conflict silently stops
# looking like a conflict. Bail out and leave the file exactly as-is.
if grep -qE '^(<{7}|>{7})( |$)' "$file" 2>/dev/null; then
  echo "format-md: skipped $file — unresolved conflict markers present (prettier would mangle them)."
  exit 0
fi

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
