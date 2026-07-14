#!/usr/bin/env python3
r"""
gen_cello.py — engrave a song's cello part (cello.ly) to print-ready sheet music.

Unlike the other charts (markdown rendered by gen_pdf.py via weasyprint), the
cello part is real staff notation written in LilyPond. This wraps the LilyPond
binary: it adds the skill's references/ dir to the include path so
`\include "cello-style.ily"` resolves from any song directory, and writes the
output PDF beside the source.

Usage:
    python gen_cello.py songs/<slug>            # renders songs/<slug>/cello.ly -> cello.pdf
    python gen_cello.py songs/<slug>/cello.ly   # explicit file
    python gen_cello.py songs/<slug> --png      # also emit a cropped PNG (preview)
    python gen_cello.py songs/<slug> --crop     # also emit a tightly-cropped PDF
    python gen_cello.py songs/<slug> --out-dir /tmp

Requires: lilypond on PATH (brew install lilypond).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
INCLUDE_DIR = SKILL_ROOT / "references"  # holds cello-style.ily


def resolve_source(arg: str) -> Path | None:
    p = Path(arg).resolve()
    if p.is_file() and p.suffix == ".ly":
        return p
    if p.is_dir():
        cand = p / "cello.ly"
        if cand.exists():
            return cand
        print(f"no cello.ly in {p}", file=sys.stderr)
        return None
    print(f"not a .ly file or directory: {p}", file=sys.stderr)
    return None


def render(src: Path, out_dir: Path, png: bool, crop: bool, svg: bool) -> int:
    lily = shutil.which("lilypond")
    if not lily:
        print("lilypond not found on PATH — `brew install lilypond`", file=sys.stderr)
        return 127

    out_base = out_dir / src.stem  # lilypond appends .pdf/.png/.cropped.*
    cmd = [lily, "-I", str(INCLUDE_DIR), "-o", str(out_base)]
    if svg:
        cmd.append("--svg")
    else:
        cmd.append("--pdf")
    if png or crop:
        cmd.append("-dcrop=#t")  # emits <base>.cropped.pdf / .cropped.png
    cmd.append(str(src))

    proc = subprocess.run(cmd, capture_output=True, text=True)
    # LilyPond chats progress on stderr; only surface it if something failed
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        print(f"lilypond failed ({proc.returncode}) on {src}", file=sys.stderr)
        return proc.returncode

    made = sorted(p for p in out_dir.glob(f"{src.stem}*")
                  if p.suffix in (".pdf", ".png", ".svg"))
    for m in made:
        print(f"Wrote {m}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("path", help="song directory or a cello.ly file")
    ap.add_argument("--png", action="store_true", help="also emit a cropped PNG preview")
    ap.add_argument("--crop", action="store_true", help="also emit a tightly-cropped PDF")
    ap.add_argument("--svg", action="store_true", help="emit SVG instead of PDF")
    ap.add_argument("--out-dir", help="write output here instead of beside the .ly")
    args = ap.parse_args()

    src = resolve_source(args.path)
    if src is None:
        return 2

    out_dir = Path(args.out_dir).resolve() if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    return render(src, out_dir, args.png, args.crop, args.svg)


if __name__ == "__main__":
    sys.exit(main())
