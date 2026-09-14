#!/usr/bin/env bash
# audit-crosslinks.sh — sanity-check [[shelf:file]] crosslinks across the
# reference shelves (convention: gpu-rosetta.md "Crosslink conventions").
#
# CHECKS:
#   FAIL  [[shelf:file]] whose target ~/.claude/references/<shelf>/<file>.md
#         doesn't exist (also catches misspelled shelf names)
#   FAIL  bare [[file]] with no <file>.md in the same directory
#   INFO  shelf-level asymmetry: shelf A links into shelf B, but B never links
#         back into A (often fine — the rosetta hub absorbs most backlinks)
#
# Usage: bash audit-crosslinks.sh [-q] [extra-dir ...]
#   Scans this repo's *.md by default; pass extra dirs (e.g. a skill's
#   references/) to audit skill-local outbound links too.
#   -q  only print FAIL lines
#
# Exit status: number of dangling links, capped at 255.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUIET=0
[[ "${1:-}" == "-q" ]] && { QUIET=1; shift; }

SCAN_DIRS=("$ROOT" "$@")
FAILS=0

# collect shelf-level edges for the asymmetry report: "srcshelf dstshelf"
EDGES=""

# [[...]] is ALSO MSL attribute syntax ([[thread_position_in_grid]]), so links
# inside fenced code blocks and inline `code spans` must be ignored.
strip_code() {
  awk 'BEGIN{f=0} /^[[:space:]]*```/{f=!f; next} !f' "$1" | sed 's/`[^`]*`//g'
}

while IFS= read -r -d '' md; do
  # source shelf = first path component under ROOT, else the literal dir
  case "$md" in
    "$ROOT"/*) src_shelf="${md#"$ROOT"/}"; src_shelf="${src_shelf%%/*}"
               [[ "$src_shelf" == *.md ]] && src_shelf="(root)" ;;
    *)         src_shelf="(external)" ;;
  esac

  # namespaced links [[shelf:file]]
  while IFS= read -r link; do
    shelf="${link%%:*}"; file="${link#*:}"
    target="$ROOT/$shelf/$file.md"
    if [[ ! -f "$target" ]]; then
      echo "FAIL  $md -> [[$link]] (no $target)"
      FAILS=$((FAILS + 1))
    else
      EDGES+="$src_shelf $shelf"$'\n'
    fi
  done < <(strip_code "$md" \
           | grep -o '\[\[[a-z0-9-]\{1,\}:[A-Za-z0-9._-]\{1,\}\]\]' 2>/dev/null \
           | sed 's/^\[\[//; s/\]\]$//')

  # bare links [[file]] resolve in the file's own directory, then the repo
  # root (home of hub files like gpu-rosetta). ONLY inside this repo: external
  # dirs (skills, archives) use bare [[name]] for OTHER namespaces (the user's
  # memory wikilinks), which aren't ours to judge.
  [[ "$src_shelf" == "(external)" ]] && continue
  while IFS= read -r link; do
    if [[ ! -f "$(dirname "$md")/$link.md" && ! -f "$ROOT/$link.md" ]]; then
      echo "FAIL  $md -> [[$link]] (no $link.md beside it or at repo root)"
      FAILS=$((FAILS + 1))
    fi
  done < <(strip_code "$md" \
           | grep -o '\[\[[A-Za-z0-9._-]\{1,\}\]\]' 2>/dev/null \
           | grep -v ':' | sed 's/^\[\[//; s/\]\]$//')
done < <(find "${SCAN_DIRS[@]}" -name '*.md' -type f -print0 2>/dev/null)

if [[ $QUIET -eq 0 && -n "$EDGES" ]]; then
  echo "--- shelf-level link graph (deduped) ---"
  printf '%s' "$EDGES" | sort -u | awk '{printf "  %s -> %s\n", $1, $2}'
  echo "--- asymmetric pairs (A->B with no B->A; rosetta/(root) excluded) ---"
  printf '%s' "$EDGES" | sort -u | awk '
    $1 != $2 && $1 != "(root)" && $1 != "(external)" { fwd[$1" "$2] = 1 }
    END { for (e in fwd) { split(e, p, " ");
          if (!((p[2]" "p[1]) in fwd)) printf "  %s -> %s (no return link)\n", p[1], p[2] } }'
fi

[[ $QUIET -eq 0 ]] && echo "dangling links: $FAILS"
exit $((FAILS > 255 ? 255 : FAILS))
