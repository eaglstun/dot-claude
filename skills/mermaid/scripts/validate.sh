#!/usr/bin/env bash
# Validate Mermaid diagrams without installing anything globally.
#
# Usage:
#   validate.sh FILE.md          Parse every ```mermaid block found in a Markdown file.
#   validate.sh FILE.mmd         Parse a standalone .mmd diagram file.
#   validate.sh -                Read a single diagram from stdin.
#
# Exit code 0 = all blocks valid; non-zero = at least one block failed.
# Requires: npx (Node). On first run it fetches @mermaid-js/mermaid-cli, then caches it.
#
# mmdc has no pure "lint" mode, so we ask it to render to SVG into a throwaway
# temp dir. A successful render == valid syntax; we discard the output.

set -uo pipefail

die() { echo "error: $*" >&2; exit 2; }

command -v npx >/dev/null 2>&1 || die "npx not found (need Node.js)"

MMDC=(npx -y @mermaid-js/mermaid-cli)

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# Parse one diagram file; returns mmdc's exit status. Output is suppressed unless it fails.
parse_one() {
    local src="$1" label="$2"
    local out="$tmpdir/out.svg" log="$tmpdir/log.txt"
    if "${MMDC[@]}" -i "$src" -o "$out" >"$log" 2>&1; then
        echo "  ok    $label"
        return 0
    else
        echo "  FAIL  $label"
        sed 's/^/        /' "$log" >&2
        return 1
    fi
}

input="${1:-}"
[ -n "$input" ] || die "no input given (pass a file, a .mmd, or - for stdin)"

fails=0

if [ "$input" = "-" ]; then
    cat > "$tmpdir/stdin.mmd"
    parse_one "$tmpdir/stdin.mmd" "(stdin)" || fails=1

elif [[ "$input" == *.mmd ]]; then
    [ -f "$input" ] || die "no such file: $input"
    parse_one "$input" "$input" || fails=1

else
    [ -f "$input" ] || die "no such file: $input"
    # Extract each ```mermaid ... ``` block into its own temp .mmd file using awk.
    count="$(awk '
        /^```mermaid[[:space:]]*$/ { inblk=1; n++; next }
        /^```[[:space:]]*$/        { if (inblk) { inblk=0 }; next }
        inblk { print > ("'"$tmpdir"'/block-" n ".mmd") }
        END { print n+0 }
    ' "$input")"

    if [ "$count" -eq 0 ]; then
        echo "no \`\`\`mermaid blocks found in $input"
        exit 0
    fi

    echo "found $count mermaid block(s) in $input"
    i=1
    while [ "$i" -le "$count" ]; do
        f="$tmpdir/block-$i.mmd"
        if [ -s "$f" ]; then
            parse_one "$f" "block #$i" || fails=1
        else
            echo "  skip  block #$i (empty)"
        fi
        i=$((i + 1))
    done
fi

if [ "$fails" -ne 0 ]; then
    echo "VALIDATION FAILED" >&2
    exit 1
fi
echo "all blocks valid"
