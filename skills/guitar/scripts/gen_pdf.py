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
from bass_tab_svg import bar_bass_notes, render_bass_phrase_svg
from chord_voicings import voicing_pool
from chart_lib import parse_lead, normalize_name, _CHORD_TOKEN_RE

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
/* `---` grouping divider — a light hairline, not weasyprint's heavy default hr */
hr { border: 0; border-top: 1px solid #ccc; height: 0; margin: 10px 0; }
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

/* lead-sheet measure boxes — equal-width bars; a full 4-bar line ≈ 3/4 page */
.barline { display: flex; align-items: center; gap: 10px; margin: 5px 0; }
table.bars { table-layout: fixed; border-collapse: collapse; margin: 0; }
table.bars td { border: 1px solid #bbb; padding: 3px 8px; font-size: 10pt;
                white-space: nowrap; text-align: left; vertical-align: middle; }
.barnote { font-weight: 650; font-size: 10pt; white-space: nowrap; color: #333; }

/* bass measure boxes — chord name over a 4-line tab staff */
table.bars.bass td { padding: 2px 2px 1px; vertical-align: top; }
.bcn { font-size: 9.5pt; font-weight: 600; white-space: nowrap; padding: 0 2px 1px; }
table.bars.bass svg { display: block; }
.lyric { margin: 3px 0 7px; font-size: 10pt; color: #444; }
.bass-intro { font-size: 10pt; color: #555; margin: 4px 0 10px; }

/* guitar measure boxes — chord name over a top-down chord diagram */
table.bars.gtr td { padding: 2px 2px 2px; vertical-align: top; }
table.bars.gtr svg { display: block; height: 92px; width: auto; margin: 1px auto 0; }
.gtr-same { font-size: 8pt; color: #b0b0b0; text-align: center; margin-top: 34px; }

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


_ANNOT_RE = re.compile(r"^\(.*\)$")

# Per-bar column width. Content area on Letter (0.6in margins) is 7.3in; four of
# these ≈ 5.6in ≈ 3/4 of the page, so a full 4-bar line lands at ~3/4 width and
# every bar is the same width everywhere (a 2-bar line is simply half as wide).
BAR_WIDTH_IN = 1.4


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bar_row_to_html(line: str) -> list[str] | None:
    """Render a lead-sheet bar row as fixed-width measure boxes (an HTML table).

    A bar row starts with `|` and contains beat marks (`//`). Its bars are the
    pipe-separated cells; a trailing parenthetical like `(2 bars)` is an
    annotation, not a bar. Behavior:

    - Every bar becomes an equal-width box (`BAR_WIDTH_IN`), so bars line up
      visually across the whole sheet regardless of chord-name length.
    - Rows longer than four bars are split into consecutive ≤4-bar lines,
      independent of where (or whether) the source put line breaks.
    - A trailing `(N bars)` annotation renders bold beside the boxes.

    Returns HTML line(s), or None if the line isn't a bar row (leave it alone).
    """
    s = line.strip()
    if not s.startswith("|") or "//" not in s:
        return None
    cells = [c.strip() for c in s.split("|")]
    # the surrounding pipes yield empty leading/trailing cells — drop them
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    # a trailing parenthetical is a "(N bars)" annotation, not a bar
    annot = None
    if cells and _ANNOT_RE.match(cells[-1]):
        annot = cells[-1]
        cells = cells[:-1]
    if not cells:
        return None
    out: list[str] = []
    for k in range(0, len(cells), 4):
        chunk = cells[k : k + 4]
        width = len(chunk) * BAR_WIDTH_IN
        tds = "".join(f"<td>{_esc(c)}</td>" for c in chunk)
        note = ""
        if annot and k + 4 >= len(cells):
            note = f'<span class="barnote">{_esc(annot)}</span>'
        out.append(
            f'<div class="barline"><table class="bars" '
            f'style="width:{width:.2f}in"><tr>{tds}</tr></table>{note}</div>'
        )
        out.append("")  # blank line closes the HTML block so a lyric below flows as its own paragraph
    return out


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
    in_fence = False  # inside a plain ``` code fence (e.g. bass tabs) — never reflow

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

        # --- track plain code fences (bass tabs) so their rows are never reflowed ---
        if (stripped.startswith("```")
                and not stripped.startswith("```chord")
                and not stripped.startswith("```keyboard")):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue

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

        # --- lead-sheet bar rows: equal-width measure boxes, ≤4 bars/line, bold (N bars) ---
        if not is_card_file and not in_fence:
            boxes = bar_row_to_html(line)
            if boxes is not None:
                out.extend(boxes)
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


def _bass_cells_and_annot(raw: str):
    """Split a raw '| ... |' bar row into (bar cells, optional (N bars) annotation)."""
    cells = [c.strip() for c in raw.strip().split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    annot = None
    if cells and _ANNOT_RE.match(cells[-1]):
        annot = cells[-1]
        cells = cells[:-1]
    return cells, annot


def _cell_chords(cell: str) -> list[str]:
    """Chord tokens in one bar cell: 'A // E //' -> ['A', 'E']."""
    return [normalize_name(tok) for tok in cell.split()
            if _CHORD_TOKEN_RE.match(tok)]


def _bass_box(cell: str) -> str:
    chords = _cell_chords(cell)
    svg = render_bass_phrase_svg(bar_bass_notes(chords)) if chords else ""
    return f'<td><div class="bcn">{_esc(cell)}</div>{svg}</td>'


def render_bass_html(lead_text: str) -> str:
    """Build the boxed bass lead sheet directly from lead.md.

    Mirrors lead.pdf's measure boxes (equal width, ≤4 bars/line, `(N bars)`
    annotations, lyrics below) but each box carries a 4-line bass tab under the
    chord name. Bass notes are computed from the chord name, so this is
    independent of chart.py.
    """
    title, sections = parse_lead(lead_text)
    out = [
        f"<h1>{_esc(title)} — Bass</h1>",
        '<p class="bass-intro">Standard tuning, low→high: '
        "<strong>E A D G</strong>. Each box is one bar — the bass note (the "
        "slash note on <code>X/Y</code>) at its lowest position, then the tones "
        "that define the chord, ascending.</p>",
    ]
    for sec in sections:
        out.append('<div class="section">')
        out.append(f"<h2>{_esc(sec.header)}</h2>")
        for row in sec.rows:
            cells, annot = _bass_cells_and_annot(row.raw)
            if not cells:
                continue
            for k in range(0, len(cells), 4):
                chunk = cells[k : k + 4]
                width = len(chunk) * BAR_WIDTH_IN
                tds = "".join(_bass_box(c) for c in chunk)
                note = ""
                if annot and k + 4 >= len(cells):
                    note = f'<span class="barnote">{_esc(annot)}</span>'
                out.append(
                    f'<div class="barline"><table class="bars bass" '
                    f'style="width:{width:.2f}in"><tr>{tds}</tr></table>{note}</div>'
                )
            if row.lyric:
                out.append(f'<p class="lyric">{_esc(row.lyric)}</p>')
        out.append("</div>")
    return "\n".join(out)


def convert_bass(lead_path: Path, out_path: Path) -> None:
    from weasyprint import HTML

    body = render_bass_html(lead_path.read_text())
    doc = build_document(body, out_path.stem)
    HTML(string=doc, base_url=str(lead_path.parent)).write_pdf(str(out_path))
    print(f"Wrote {out_path}")


def _section_voicings(sections) -> dict:
    """Assign each (section index, chord) a voicing, advancing the chord's
    position one step for every new section it appears in."""
    from collections import defaultdict

    seen: dict[str, int] = defaultdict(int)
    assigned: dict[tuple[int, str], list] = {}
    for si, sec in enumerate(sections):
        uniq: list[str] = []
        for row in sec.rows:
            for cell in _bass_cells_and_annot(row.raw)[0]:
                for c in _cell_chords(cell):
                    if c not in uniq:
                        uniq.append(c)
        for c in uniq:
            pool = voicing_pool(c)
            if not pool:
                continue
            assigned[(si, c)] = pool[min(seen[c], len(pool) - 1)]
            seen[c] += 1
    return assigned


def render_guitar_html(lead_text: str) -> str:
    """Boxed guitar chart from lead.md: chord name over a top-down diagram.

    Same measure boxes as lead/bass. A diagram is drawn only when the voicing
    changes (repeated bars just hold it); each chord advances to a more
    interesting position every new section it appears in.
    """
    title, sections = parse_lead(lead_text)
    assigned = _section_voicings(sections)

    out = [
        f"<h1>{_esc(title)} — Guitar</h1>",
        '<p class="bass-intro">Chord voicings, low→high '
        "<strong>E A D G B E</strong>. A shape is drawn when it changes; repeated "
        "bars hold it. Each chord moves to a fresh position as it returns in later "
        "sections.</p>",
    ]
    prev = [None]  # last displayed (chord, voicing) — mutable holder for the closure

    def box(cell: str, si: int) -> str:
        label = f'<div class="bcn">{_esc(cell)}</div>'
        chords = _cell_chords(cell)
        if len(chords) != 1:  # split or empty bar breaks the run
            prev[0] = None
            return f"<td>{label}</td>"
        v = assigned.get((si, chords[0]))
        if v is None:
            prev[0] = None
            return f"<td>{label}</td>"
        key = (chords[0], tuple(x if x is None else int(x) for x in v))
        if key == prev[0]:
            return f'<td>{label}<div class="gtr-same">⟍</div></td>'
        prev[0] = key
        return f"<td>{label}{render_chord_svg(v)}</td>"

    for si, sec in enumerate(sections):
        prev[0] = None  # re-establish shapes at the top of each section
        out.append('<div class="section">')
        out.append(f"<h2>{_esc(sec.header)}</h2>")
        for row in sec.rows:
            cells, annot = _bass_cells_and_annot(row.raw)
            if not cells:
                continue
            for k in range(0, len(cells), 4):
                chunk = cells[k : k + 4]
                width = len(chunk) * BAR_WIDTH_IN
                tds = "".join(box(c, si) for c in chunk)
                note = ""
                if annot and k + 4 >= len(cells):
                    note = f'<span class="barnote">{_esc(annot)}</span>'
                out.append(
                    f'<div class="barline"><table class="bars gtr" '
                    f'style="width:{width:.2f}in"><tr>{tds}</tr></table>{note}</div>'
                )
            if row.lyric:
                out.append(f'<p class="lyric">{_esc(row.lyric)}</p>')
        out.append("</div>")
    return "\n".join(out)


def convert_guitar(lead_path: Path, out_path: Path) -> None:
    from weasyprint import HTML

    body = render_guitar_html(lead_path.read_text())
    doc = build_document(body, out_path.stem)
    HTML(string=doc, base_url=str(lead_path.parent)).write_pdf(str(out_path))
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

    p = Path(args.path).resolve()

    # `guitar` is a virtual target — built from lead.md, no guitar.md on disk.
    if args.files:
        want_guitar = "guitar" in args.files
        md_files = [f for f in args.files if f != "guitar"]
        targets = resolve_targets(args.path, md_files) if md_files else []
    else:
        want_guitar = p.is_dir() and (p / "lead.md").exists()
        targets = resolve_targets(args.path, None)

    if not targets and not want_guitar:
        return 2

    out_dir = Path(args.out_dir).resolve() if args.out_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    for md in targets:
        dest = (out_dir or md.parent) / f"{md.stem}.pdf"
        if md.stem == "bass":
            # the boxed bass chart is built from lead.md, not bass.md
            lead = md.parent / "lead.md"
            if not lead.exists():
                print(f"skip bass.pdf: no lead.md beside {md}", file=sys.stderr)
                continue
            convert_bass(lead, dest)
        else:
            convert(md, dest)

    if want_guitar:
        lead = p if p.name == "lead.md" else p / "lead.md"
        if not p.is_dir() and p.name != "lead.md":
            lead = p.parent / "lead.md"
        if lead.exists():
            convert_guitar(lead, (out_dir or lead.parent) / "guitar.pdf")
        else:
            print("skip guitar.pdf: no lead.md found", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
