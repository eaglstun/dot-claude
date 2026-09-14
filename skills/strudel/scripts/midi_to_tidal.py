#!/usr/bin/env python3
"""Transcribe a MIDI part into per-bar TidalCycles mini-notation.

The Tidal sibling of midi_to_strudel.py. Quantizes note onsets to a grid and
emits Haskell bindings: a [String] of one mini-notation bar per cycle, plus a
ready-made ControlPattern that `cat`s them.

Two things differ from the Strudel script, and both will bite silently:

  * OCTAVES. Tidal's note parser defaults to octave 5, so `c5` == `c` == 0 ==
    middle C == MIDI 60. (Verified by querying tidal-1.10.1: c5 -> 0.0,
    c4 -> -12.0.) The Strudel script emits MIDI 60 as `c4`, which Tidal reads
    as -12 — the whole part plays an octave low and sounds entirely plausible
    the whole time. Here MIDI 60 -> `c5`. Override with --octave-offset.
  * SHARPS. Tidal spells them `cs`/`df`, not `c#`. Emitted directly, so no
    `m()`-style fixup helper is needed at the far end.

Beyond that it does what the Strudel one couldn't: chords (mini-notation
`[c5,e5,g5]`) and note length (a parallel `legato` pattern built from the
durations the grid would otherwise throw away).

Usage:
    python3 midi_to_tidal.py FILE.mid --list-tracks
    python3 midi_to_tidal.py FILE.mid [--track N] [--grid 16] [--name bass]
                                      [--legato] [--mono] [--numeric]
                                      [--first-bar 1] [--last-bar 148]

What this does NOT do is make the result idiomatic Tidal. A flat 16-slot grid
is a piano roll written in text: correct, and inert under `jux rev` or
`every 3 (fast 2)` because there is no structure to grab. Getting the notes
right is this script's job; collapsing repeats into `<c5 e5>`, spotting where a
rhythm is really `euclid 3 8`, and splitting bars into `[a2 ~]*2` is a hand
pass afterwards. That pass is the composition.
"""
import argparse
import re
import sys
from collections import defaultdict

try:
    import mido
except ImportError:
    sys.exit("mido not installed — run: pip3 install mido")

# Tidal spells accidentals with s/f. Sharps chosen arbitrarily; both parse
# (cs5 and df5 both query to 1.0).
NAMES = ["c", "cs", "d", "ds", "e", "f", "fs", "g", "gs", "a", "as", "b"]

# MIDI 60 -> "c5". Tidal's default octave is 5, NOT the general-MIDI 4.
TIDAL_OCTAVE_OFFSET = 0


def note_name(pitch, octave_offset):
    return f"{NAMES[pitch % 12]}{pitch // 12 + octave_offset}"


def read_notes(path):
    """Return (notes, ticks_per_beat, beats_per_bar, track_names).

    notes: list of (track, start_tick, end_tick, pitch, velocity)

    Pairs note_on/note_off per (track, channel, pitch) so durations survive.
    A note_on with velocity 0 is a note_off, which is how plenty of DAWs and
    every General MIDI running-status file write it.
    """
    try:
        mid = mido.MidiFile(path)
    except FileNotFoundError:
        sys.exit(f"no such file: {path}")
    except (OSError, ValueError, EOFError) as exc:
        sys.exit(f"could not read {path} as MIDI: {exc}")
    notes = []
    names = []
    beats_per_bar = None

    for ti, track in enumerate(mid.tracks):
        names.append(track.name or f"track {ti}")
        t = 0
        pending = defaultdict(list)  # (channel, pitch) -> [(start, velocity)]
        for msg in track:
            t += msg.time
            if msg.type == "time_signature" and beats_per_bar is None:
                # In quarter-note beats: 6/8 is 3 quarter-note beats per bar.
                beats_per_bar = msg.numerator * 4 / msg.denominator
            elif msg.type == "note_on" and msg.velocity > 0:
                pending[(msg.channel, msg.note)].append((t, msg.velocity))
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                stack = pending.get((msg.channel, msg.note))
                if stack:
                    start, vel = stack.pop(0)
                    notes.append((ti, start, t, msg.note, vel))
        # Unterminated notes (truncated export) still count; end them at the
        # last tick seen rather than dropping them.
        for (_, pitch), stack in pending.items():
            for start, vel in stack:
                notes.append((ti, start, max(t, start + 1), pitch, vel))

    notes.sort(key=lambda n: (n[1], n[3]))
    return notes, mid.ticks_per_beat, beats_per_bar, names


def list_tracks(path):
    notes, tpb, bpb, names = read_notes(path)
    counts = defaultdict(int)
    lo = {}
    hi = {}
    for ti, _, _, pitch, _ in notes:
        counts[ti] += 1
        lo[ti] = min(lo.get(ti, 127), pitch)
        hi[ti] = max(hi.get(ti, 0), pitch)
    print(f"# {path}")
    print(f"# ticks/beat={tpb}  beats/bar={bpb or 4}  tracks={len(names)}")
    for ti, name in enumerate(names):
        if not counts[ti]:
            print(f"  [{ti}] {name!r:28} (no notes)")
            continue
        print(f"  [{ti}] {name!r:28} notes={counts[ti]:5} "
              f"range={note_name(lo[ti], TIDAL_OCTAVE_OFFSET)}"
              f"..{note_name(hi[ti], TIDAL_OCTAVE_OFFSET)}")


def quantize(notes, tpb, beats_per_bar, grid, tracks):
    """Bucket notes into (bar, slot). Returns {(bar, slot): [note, ...]}."""
    slot_beats = beats_per_bar / grid
    buckets = defaultdict(list)
    for ti, start, end, pitch, vel in notes:
        if tracks is not None and ti not in tracks:
            continue
        beat = start / tpb
        bar = int(beat // beats_per_bar) + 1
        in_bar = beat - (bar - 1) * beats_per_bar
        slot = round(in_bar / slot_beats)
        if slot >= grid:  # an anticipation that rounds past the barline
            bar += 1
            slot = 0
        buckets[(bar, slot)].append((pitch, (end - start) / tpb, vel))
    return buckets


def render_bars(buckets, first_bar, last_bar, grid, args):
    """Return (note_bars, legato_bars) as lists of mini-notation strings."""
    note_bars, legato_bars = [], []
    slot_beats = args.beats_per_bar / grid

    for bar in range(first_bar, last_bar + 1):
        slots, legs = [], []
        occupied = False
        for s in range(grid):
            hits = buckets.get((bar, s))
            if not hits:
                slots.append("~")
                legs.append("~")
                continue
            occupied = True

            # Dedupe pitches (layered/doubled tracks repeat them), lowest first.
            seen, uniq = set(), []
            for pitch, dur, vel in sorted(hits):
                if pitch in seen:
                    continue
                seen.add(pitch)
                uniq.append((pitch, dur, vel))

            keep = uniq[:1] if args.mono else uniq[: args.max_voices]

            if args.numeric:
                tokens = [str(p - 60 + args.transpose) for p, _, _ in keep]
            else:
                tokens = [note_name(p + args.transpose, args.octave_offset)
                          for p, _, _ in keep]
            slots.append(tokens[0] if len(tokens) == 1 else "[" + ",".join(tokens) + "]")

            # legato multiplies the event's own step length, so the value is
            # the note's duration measured in grid slots. Longest voice wins.
            ratio = max(d for _, d, _ in keep) / slot_beats
            legs.append(f"{ratio:.3g}")

        note_bars.append(" ".join(slots) if occupied else "~")
        legato_bars.append(" ".join(legs) if occupied else "~")

    return note_bars, legato_bars


def hs_name(raw):
    """Make a legal lowerCamelCase Haskell binding name."""
    parts = [p for p in re.split(r"[^0-9a-zA-Z]+", raw) if p]
    if not parts:
        parts = ["part"]
    # Lowercase only the first character, so a name already in camelCase
    # ("gameBass") survives instead of being flattened to "gamebass".
    head = parts[0][0].lower() + parts[0][1:]
    name = head + "".join(p[0].upper() + p[1:] for p in parts[1:])
    if not name[0].isalpha():
        name = "p" + name
    return name


def main():
    ap = argparse.ArgumentParser(
        description="MIDI -> TidalCycles mini-notation.")
    ap.add_argument("file")
    ap.add_argument("--list-tracks", action="store_true",
                    help="print track names, note counts and ranges, then exit")
    ap.add_argument("--track", default=None,
                    help="track index, or comma-separated list (default: all)")
    ap.add_argument("--grid", type=int, default=16, help="slots per bar")
    ap.add_argument("--beats-per-bar", type=float, default=None,
                    help="default: read the file's time signature, else 4")
    ap.add_argument("--first-bar", type=int, default=1)
    ap.add_argument("--last-bar", type=int, default=None)
    ap.add_argument("--name", default=None,
                    help="Haskell binding name (default: from filename/track)")
    ap.add_argument("--module", default=None, metavar="NAME",
                    help="emit a module header + import so the output is a "
                         "`:load`-able file (save it as NAME.hs). Without this "
                         "the output is a bare snippet to paste into a session.")
    ap.add_argument("--mono", action="store_true",
                    help="keep only the lowest voice per slot (no chords)")
    ap.add_argument("--max-voices", type=int, default=4,
                    help="cap stacked notes per slot, lowest kept (default 4)")
    ap.add_argument("--legato", action="store_true",
                    help="also emit a legato pattern carrying note lengths")
    ap.add_argument("--numeric", action="store_true",
                    help="emit semitone numbers (middle C = 0) not note names")
    ap.add_argument("--transpose", type=int, default=0, help="semitones")
    ap.add_argument("--octave-offset", type=int, default=TIDAL_OCTAVE_OFFSET,
                    help="octave numbering; 0 = Tidal (MIDI 60 -> c5). "
                         "Use -1 for general-MIDI naming (MIDI 60 -> c4).")
    args = ap.parse_args()

    if args.list_tracks:
        list_tracks(args.file)
        return

    notes, tpb, file_bpb, names = read_notes(args.file)
    if not notes:
        sys.exit(f"no notes found in {args.file}")

    if args.beats_per_bar is None:
        args.beats_per_bar = file_bpb or 4.0

    tracks = None
    if args.track is not None:
        tracks = {int(x) for x in args.track.split(",")}
        bad = tracks - set(range(len(names)))
        if bad:
            sys.exit(f"no such track(s): {sorted(bad)} (file has 0..{len(names)-1})")

    buckets = quantize(notes, tpb, args.beats_per_bar, args.grid, tracks)
    if not buckets:
        sys.exit("no notes left after track filtering")

    last_bar = args.last_bar or max(b for b, _ in buckets)
    note_bars, legato_bars = render_bars(
        buckets, args.first_bar, last_bar, args.grid, args)

    base = args.name or (re.sub(r"\.midi?$", "", args.file.split("/")[-1])
                         + ("" if tracks is None else
                            "-" + names[min(tracks)]))
    var = hs_name(base)

    src = args.file
    if tracks is not None:
        src += "  tracks " + ", ".join(f"[{t}] {names[t]!r}" for t in sorted(tracks))

    out = []
    if args.module:
        out.append(f"module {args.module} where")
        out.append("")
        out.append("import Sound.Tidal.Context")
        out.append("")
    out.append(f"-- Generated by midi_to_tidal.py from {src}")
    out.append(f"-- {len(note_bars)} bars (source bars {args.first_bar}-{last_bar}), "
               f"{args.grid} slots/bar, {args.beats_per_bar:g} beats/bar")
    out.append(f"-- 1 cycle == 1 bar. Middle C is c5 "
               f"(octave offset {args.octave_offset}).")
    out.append(f"-- $ python3 {' '.join(sys.argv[1:])}")
    out.append("")
    out.append(f"{var} :: [String]")
    out.append(f"{var} =")
    for i, bar in enumerate(note_bars):
        lead = "  [ " if i == 0 else "  , "
        out.append(f'{lead}"{bar}"')
    out.append("  ]")
    out.append("")

    if args.legato:
        lvar = var + "Legato"
        out.append(f"{lvar} :: [String]")
        out.append(f"{lvar} =")
        for i, bar in enumerate(legato_bars):
            lead = "  [ " if i == 0 else "  , "
            out.append(f'{lead}"{bar}"')
        out.append("  ]")
        out.append("")
        out.append(f"{var}P :: ControlPattern")
        out.append(f"{var}P = cat (zipWith step {var} {lvar})")
        out.append("  where step n l = note (parseBP_E n) # legato (parseBP_E l)")
    else:
        out.append(f"{var}P :: ControlPattern")
        out.append(f"{var}P = cat (map (note . parseBP_E) {var})")

    out.append("")
    out.append(f"-- d1 $ {var}P # s \"superpiano\"")
    print("\n".join(out))


if __name__ == "__main__":
    main()
