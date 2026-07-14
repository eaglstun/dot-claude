#!/usr/bin/env python3
"""
gen_pdf.py — render OWNER/OPERATORS chart Markdown to print-ready PDF.

Converts lead.md / chords.md / bass.md / drums.md to PDFs. The ASCII
```chord``` blocks in chords.md are replaced with real SVG fretboard diagrams
(see chord_svg.py); guitar chords are laid out as a card grid; bass tabs stay
monospace. Output is US Letter, ready to print or share.

Usage:
    python gen_pdf.py <song-dir>                 # all known .md files in the dir
    python gen_pdf.py <song-dir> --files chords  # just chords.pdf
    python gen_pdf.py path/to/lead.md            # a single file -> lead.pdf
    python gen_pdf.py <song-dir> --out-dir /tmp  # write PDFs elsewhere

Requires: weasyprint, markdown-it-py (both already installed).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from chord_svg import parse_voicing, render_chord_svg
from keyboard_svg import render_keyboard_svg

KNOWN_FILES = ["lead.md", "chords.md", "bass.md", "drums.md", "keys.md"]

CSS = """
@page { size: Letter; margin: 0.6in; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
       color: #1a1a1a; font-size: 11pt; line-height: 1.42; }
h1 { font-size: 21pt; margin: 0 0 12px; padding-bottom: 5px;
     border-bottom: 2px solid #222; }
h2 { font-size: 13pt; margin: 18px 0 8px; color: #333;
     border-bottom: 1px solid #ddd; padding-bottom: 2px; }
h3 { font-size: 11.5pt; margin: 0 0 3px; }
h3 em { color: #8a8a8a; font-weight: normal; font-style: italic; font-size: 9.5pt; }
p { margin: 6px 0; }
strong { font-weight: 650; }
a { color: #1a1a1a; text-decoration: none; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt;
        break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 4px 8px; text-align: left; vertical-align: top; }
th { background: #f2f2f2; }
pre { background: #fafafa; border: 1px solid #e4e4e4; border-radius: 4px;
      padding: 8px 11px; font-family: "SF Mono", Menlo, Consolas, monospace;
      font-size: 9.5pt; line-height: 1.35; white-space: pre; break-inside: avoid; }
code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 9.5pt; }
pre code { font-size: inherit; }

/* guitar chord cards — three across, never split across a page */
.chord-card { display: inline-block; vertical-align: top; width: 31.5%;
              margin: 0 1% 10px 0; padding: 8px 8px 4px; border: 1px solid #e3e3e3;
              border-radius: 8px; break-inside: avoid; text-align: center; }
.chord-card h3 { white-space: nowrap; text-align: center; }
.chord-card p { margin: 1px 0 5px; font-family: "SF Mono", Menlo, monospace;
                font-size: 8.5pt; color: #666; }
.chord-wrap { text-align: center; line-height: 0; }
.chord-wrap svg { height: 100px; width: auto; }

/* piano chord diagrams — fill the card width */
.kbd-wrap { text-align: center; line-height: 0; margin: 3px 0 2px; }
.kbd-wrap svg { width: 100%; height: auto; }

/* piano keyboard cards — four across (vs guitar's three) */
.kbd-card { display: inline-block; vertical-align: top; width: 23%;
            margin: 0 1% 10px 0; padding: 8px 6px 4px; border: 1px solid #e3e3e3;
            border-radius: 8px; break-inside: avoid; text-align: center; }
.kbd-card h3 { white-space: nowrap; text-align: center; font-size: 10.5pt; }

/* per-section lyrics — quoted italics so keys can track the singer */
blockquote { margin: 4px 0 9px; padding: 3px 0 3px 11px; border-left: 3px solid #d8d8d8;
             color: #555; font-style: italic; font-size: 10pt; line-height: 1.5;
             break-inside: avoid; }
blockquote p { margin: 0; }

h2 { break-after: avoid; }

/* keep a whole section (header + its rows) together on one page */
.section { break-inside: avoid; }

/* the quick-reference section starts on a fresh page */
.quickref { break-before: page; }
"""

_HEADING_RE = re.compile(r"^(#{1,6})\s")
_FENCE_RE = re.compile(r"^```")
_QUICKREF_RE = re.compile(r"^#{1,6}\s+(Quick reference.*)$", re.I)


def _find_voicing_above(lines: list[str], block_start: int) -> list | None:
    """Scan upward from a ```chord fence for the nearest voicing line."""
    for k in range(block_start - 1, max(-1, block_start - 6), -1):
        s = lines[k].strip()
        if not s:
            continue
        v = parse_voicing(s)
        if v is not None:
            return v
        # a heading or another fence means we've left the voicing's neighborhood
        if _HEADING_RE.match(s) or s.startswith("```"):
            break
    return None


def preprocess(text: str) -> str:
    """Replace ```chord blocks with SVG and wrap guitar chords in cards.

    Card wrapping only happens for files that actually contain ```chord blocks
    (i.e. chords.md), so lead/bass/drums flow normally.
    """
    lines = text.split("\n")
    is_card_file = any(l.strip().startswith("```chord") or
                       l.strip().startswith("```keyboard") for l in lines)
    # keyboards pack 4-across (kbd-card); guitar fretboards stay 3-across (chord-card)
    is_keyboard_file = any(l.strip().startswith("```keyboard") for l in lines)
    card_class = "kbd-card" if is_keyboard_file else "chord-card"

    out: list[str] = []
    card_open = False
    section_open = False

    def close_card():
        nonlocal card_open
        if card_open:
            out.extend(["", "</div>", ""])
            card_open = False

    def close_section():
        nonlocal section_open
        if section_open:
            out.extend(["", "</div>", ""])
            section_open = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # --- quick-reference heading: force onto its own page ---
        qr = _QUICKREF_RE.match(stripped)
        if qr:
            close_card()
            close_section()
            out.extend(["", f'<h2 class="quickref">{qr.group(1)}</h2>', ""])
            i += 1
            continue

        # --- replace a ```keyboard block with a piano-chord SVG ---
        if stripped.startswith("```keyboard"):
            j = i + 1
            spec = None
            while j < len(lines) and not _FENCE_RE.match(lines[j].strip()):
                if lines[j].strip() and spec is None:
                    spec = lines[j].strip()
                j += 1
            if spec:
                svg = render_keyboard_svg(spec.split())
                out.extend(["", f'<div class="kbd-wrap">{svg}</div>', ""])
            i = j + 1
            continue

        # --- replace a ```chord block with an SVG diagram ---
        if stripped.startswith("```chord"):
            j = i + 1
            while j < len(lines) and not _FENCE_RE.match(lines[j].strip()):
                j += 1
            voicing = _find_voicing_above(lines, i)
            if voicing is not None:
                svg = render_chord_svg(voicing)
                out.extend(["", f'<div class="chord-wrap">{svg}</div>', ""])
            else:
                # couldn't find the voicing — keep the original ASCII block
                out.extend(lines[i : j + 1])
            i = j + 1
            continue

        # --- section wrapping for flow files (lead/bass/drums/keys) ---
        # Wrap each `## Section` and its rows in a div so a page break never
        # falls in the middle of a section. (Card files group by ### instead.)
        if not is_card_file:
            m = _HEADING_RE.match(stripped)
            if m and len(m.group(1)) <= 2:
                close_section()
                if len(m.group(1)) == 2:  # h2 opens a new section; h1 (title) doesn't
                    out.extend(["", '<div class="section">', ""])
                    section_open = True
                out.append(line)
                i += 1
                continue

        # --- card wrapping for diagram files ---
        if is_card_file:
            m = _HEADING_RE.match(stripped)
            if m:
                level = len(m.group(1))
                if level == 3:
                    close_card()
                    out.extend(["", f'<div class="{card_class}">', ""])
                    card_open = True
                    out.append(line)
                    i += 1
                    continue
                else:  # h1/h2 (and the quick-ref table) end the current card run
                    close_card()
                    out.append(line)
                    i += 1
                    continue

        out.append(line)
        i += 1

    close_card()
    close_section()
    return "\n".join(out)


def md_to_html(text: str, hard_breaks: bool = False) -> str:
    from markdown_it import MarkdownIt

    # Flow files (lead/bass/drums) stack chord row / lyric / cue as adjacent
    # lines of one paragraph — render those line breaks for real so the PDF
    # matches the .md layout instead of merging them into one wrapped line.
    md = MarkdownIt("commonmark",
                    {"html": True, "breaks": hard_breaks}).enable("table")
    return md.render(text)


def build_document(body_html: str, title: str) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title><style>{CSS}</style></head>"
        f"<body>{body_html}</body></html>"
    )


def convert(md_path: Path, out_path: Path) -> None:
    from weasyprint import HTML

    text = md_path.read_text()
    processed = preprocess(text)
    is_card_file = "```chord" in text or "```keyboard" in text
    body = md_to_html(processed, hard_breaks=not is_card_file)
    doc = build_document(body, md_path.stem)
    HTML(string=doc, base_url=str(md_path.parent)).write_pdf(str(out_path))
    print(f"Wrote {out_path}")


def resolve_targets(arg: str, files: list[str] | None) -> list[Path]:
    p = Path(arg).resolve()
    if p.is_file() and p.suffix == ".md":
        return [p]
    if p.is_dir():
        if files:
            wanted = [f if f.endswith(".md") else f"{f}.md" for f in files]
        else:
            wanted = KNOWN_FILES
        return [p / w for w in wanted if (p / w).exists()]
    print(f"not a .md file or directory: {p}", file=sys.stderr)
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="song directory or a single .md file")
    ap.add_argument("--files", nargs="+",
                    help="subset to convert, e.g. --files lead chords")
    ap.add_argument("--out-dir", help="write PDFs here instead of beside the .md")
    args = ap.parse_args()

    targets = resolve_targets(args.path, args.files)
    if not targets:
        return 2

    out_dir = Path(args.out_dir).resolve() if args.out_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    for md in targets:
        dest = (out_dir or md.parent) / f"{md.stem}.pdf"
        convert(md, dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
