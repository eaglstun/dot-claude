#!/usr/bin/env python3
"""Dump a Standard MIDI File as note events, quantized to beats and bars.

Purpose: read a MIDI part (e.g. a bassline a player tracked in a DAW) and print
it in a shape that's easy to translate into Strudel mini-notation — note names,
which bar each note lands in, and start/length measured in beats.

Usage:
    python3 dump_midi.py FILE.mid [--beats-per-bar 4] [--track N]

Output is one line per note:
    bar  beat   len(beats)  name   (vel)
Plus a per-bar grouped view at the end (handy for building `cat(...)` bars).

Needs `mido` (pip install mido). Pure file parsing — no live MIDI I/O, so
python-rtmidi is NOT required.
"""
import argparse
import sys

try:
    import mido
except ImportError:
    sys.exit("mido not installed — run: pip install mido")

# MIDI note number -> Strudel-style name. Strudel writes sharps as `s` (cs3),
# but we emit `#` here for readability; convert with .replaceAll('#','s') when
# you paste into a pattern (the song file already has an `m()` helper for that).
NAMES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]


def note_name(n):
    return f"{NAMES[n % 12]}{n // 12 - 1}"  # MIDI 60 = c4 (Strudel convention)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--beats-per-bar", type=int, default=4)
    ap.add_argument("--track", type=int, default=None,
                    help="only this track index (default: merge all)")
    args = ap.parse_args()

    mid = mido.MidiFile(args.file)
    tpb = mid.ticks_per_beat
    bpbar = args.beats_per_bar

    tracks = [mid.tracks[args.track]] if args.track is not None else mid.tracks

    # Flatten to absolute-tick note_on/note_off events.
    notes = []          # (start_tick, end_tick, pitch, velocity)
    for tr in tracks:
        t = 0
        active = {}     # pitch -> (start_tick, velocity)
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                active[msg.note] = (t, msg.velocity)
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                if msg.note in active:
                    start, vel = active.pop(msg.note)
                    notes.append((start, t, msg.note, vel))

    notes.sort()
    if not notes:
        sys.exit("no notes found (wrong --track? try omitting it)")

    print(f"# {args.file}")
    print(f"# ticks/beat={tpb}  beats/bar={bpbar}  notes={len(notes)}")
    print(f"# {'bar':>4} {'beat':>6} {'len':>6}  name   vel")
    rows = []
    for start, end, pitch, vel in notes:
        beat_pos = start / tpb
        length = (end - start) / tpb
        bar = int(beat_pos // bpbar) + 1
        beat = beat_pos % bpbar
        rows.append((bar, beat, length, pitch, vel))
        print(f"  {bar:>4} {beat:>6.2f} {length:>6.2f}  {note_name(pitch):<5} ({vel})")

    # Per-bar grouped view — each note as name@beat for quick mini-notation work.
    print("\n# per-bar (name@beat ·len):")
    last_bar = None
    for bar, beat, length, pitch, vel in rows:
        if bar != last_bar:
            print(f"\nbar {bar:>3}: ", end="")
            last_bar = bar
        print(f"{note_name(pitch)}@{beat:.2f}·{length:.2f}  ", end="")
    print()


if __name__ == "__main__":
    main()
