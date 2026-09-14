#!/usr/bin/env python3
"""Transcribe a monophonic-ish MIDI part into per-bar Strudel mini-notation.

Quantizes note onsets to a grid (default 16th notes) and emits one mini-notation
string per bar — e.g. "d3 ~ ~ a2 d3 ~ ~ ~ ...". Rests are `~`. Designed for
turning a tracked bass/lead into a `cat(...)` of bars that lines up with a song
whose 1 cycle == 1 bar.

Usage:
    python3 midi_to_strudel.py FILE.mid [--grid 16] [--beats-per-bar 4]
                                        [--first-bar 10] [--last-bar 148]
                                        [--var NAME]

--first-bar/--last-bar pad/trim so bar 1 of the song maps to slot 0 of output
(bars before --first-bar become silence). Emits a JS array literal.

Note names use `#`; the song's `m()` helper converts `#`->`s` at build time.
"""
import argparse
import sys

try:
    import mido
except ImportError:
    sys.exit("mido not installed — run: pip install mido")

NAMES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]


def note_name(n):
    return f"{NAMES[n % 12]}{n // 12 - 1}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--grid", type=int, default=16, help="slots per bar")
    ap.add_argument("--beats-per-bar", type=int, default=4)
    ap.add_argument("--first-bar", type=int, default=1)
    ap.add_argument("--last-bar", type=int, default=None)
    ap.add_argument("--var", default="BASS_MIDI")
    args = ap.parse_args()

    mid = mido.MidiFile(args.file)
    tpb = mid.ticks_per_beat
    slot_beats = args.beats_per_bar / args.grid  # beats per grid slot

    # Collect note onsets (absolute ticks) across all tracks.
    onsets = []  # (tick, pitch)
    for tr in mid.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                onsets.append((t, msg.note))
    onsets.sort()

    # Quantize each onset to (bar, slot). Keep earliest note per slot.
    grid = {}  # (bar, slot) -> pitch
    for tick, pitch in onsets:
        beat = tick / tpb
        bar = int(beat // args.beats_per_bar) + 1
        in_bar = beat - (bar - 1) * args.beats_per_bar
        slot = round(in_bar / slot_beats)
        if slot >= args.grid:          # anticipation past the barline
            slot = args.grid - 1
        grid.setdefault((bar, slot), pitch)

    last_bar = args.last_bar or (max(b for b, _ in grid) if grid else args.first_bar)

    bars = []
    for bar in range(args.first_bar, last_bar + 1):
        if not any((bar, s) in grid for s in range(args.grid)):
            bars.append("~")  # whole-bar rest
            continue
        slots = [note_name(grid[(bar, s)]) if (bar, s) in grid else "~"
                 for s in range(args.grid)]
        bars.append(" ".join(slots))

    print(f"// {args.file}")
    print(f"// {len(bars)} bars, {args.grid}-slot grid (bars {args.first_bar}-{last_bar})")
    print(f"export const {args.var} = [")
    for bar in bars:
        print(f'  "{bar}",')
    print("];")


if __name__ == "__main__":
    main()
