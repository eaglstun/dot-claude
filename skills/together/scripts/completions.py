#!/usr/bin/env python3
"""Together legacy text completions (POST /v1/completions).

Raw prompt in, text out at choices[0].text. Prefer chat.py for instruction-tuned
models; use this for base models / raw-prompt control.

Usage:
  completions.py "The largest city in France is"
                 [--model meta-llama/Llama-3.3-70B-Instruct-Turbo]
                 [--max-tokens N] [--temperature F] [--stop S ...]

Prints the completion text to stdout. Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse
from _common import post_json

DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--stop", nargs="*")
    args = ap.parse_args()

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }
    if args.stop:
        payload["stop"] = args.stop

    resp = post_json("/v1/completions", payload)
    print(resp["choices"][0]["text"])


if __name__ == "__main__":
    main()
