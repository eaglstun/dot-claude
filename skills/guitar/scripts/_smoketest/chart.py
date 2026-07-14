"""Smoke test: tiny one-chord song to validate gen_chart.py end-to-end."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chart_lib import Chord, Song

SONG = Song(
    title="Smoke Test",
    sections=[
        ("Intro", ["Bm", "Bm"]),
        ("Verse 1", ["Bm", "G"]),
    ],
)

CHORDS = {
    "Bm": Chord(
        family="B minor",
        guitar="x 2 4 4 3 2",
        guitar_note="barre 2nd fret, Am shape",
        bass_low=["A-2", "E-7"],
        bass_high=["G-4", "D-9"],
    ),
    "G": Chord(
        family="G",
        guitar="3 2 0 0 3 3",
        bass_low=["E-3", "A-2"],
        bass_high=["D-5", "A-5"],
    ),
}

BASS_CUES = {
    "G": "Smoke-test cue — lands on the first Verse 1 row.",
}
