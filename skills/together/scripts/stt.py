#!/usr/bin/env python3
"""Together speech-to-text: transcription or translation-to-English.

Usage:
  stt.py audio.mp3                       # transcribe (original language)
  stt.py audio.mp3 --translate           # translate foreign speech -> English
  stt.py https://host/clip.mp3           # a public URL also works
      [--model openai/whisper-large-v3] [--language auto] [--prompt BIAS]
      [--response-format json|verbose_json] [--verbose-json]

Prints the transcript text (json) or the full JSON (verbose_json) to stdout.
Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse, json
from _common import post_multipart

DEFAULT_MODEL = "openai/whisper-large-v3"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="audio file path or public https URL")
    ap.add_argument("--translate", action="store_true",
                    help="translate to English instead of transcribing")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--language", default=None, help="ISO 639-1 code or 'auto'")
    ap.add_argument("--prompt", default=None, help="bias text (Whisper only)")
    ap.add_argument("--response-format", default="json",
                    choices=["json", "verbose_json"])
    ap.add_argument("--verbose-json", action="store_true",
                    help="shortcut for --response-format verbose_json")
    args = ap.parse_args()

    rfmt = "verbose_json" if args.verbose_json else args.response_format
    path = "/v1/audio/translations" if args.translate else "/v1/audio/transcriptions"
    fields = {"model": args.model, "response_format": rfmt,
              "language": args.language, "prompt": args.prompt}

    resp = post_multipart(path, fields, file_field="file", file_path=args.file)
    if rfmt == "verbose_json":
        print(json.dumps(resp, indent=2))
    else:
        print(resp["text"])


if __name__ == "__main__":
    main()
