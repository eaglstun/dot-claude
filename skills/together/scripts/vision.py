#!/usr/bin/env python3
"""Together vision chat (POST /v1/chat/completions with image content).

Usage:
  vision.py "Describe this image." --image https://example.com/img.png
  vision.py "What's wrong here?"   --image ./local.jpg   # local file -> data URL
      [--model meta-llama/Llama-Vision-Free] [--max-tokens N]

Multiple --image flags are allowed. Prints the model's answer to stdout.
Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse, base64, mimetypes
from _common import post_json

DEFAULT_MODEL = "meta-llama/Llama-Vision-Free"


def to_url(ref: str) -> str:
    if ref.startswith(("http://", "https://", "data:")):
        return ref
    mime = mimetypes.guess_type(ref)[0] or "image/png"
    with open(ref, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--image", action="append", required=True,
                    help="image URL or local path (repeatable)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-tokens", type=int, default=1024)
    args = ap.parse_args()

    content = [{"type": "text", "text": args.prompt}]
    for ref in args.image:
        content.append({"type": "image_url", "image_url": {"url": to_url(ref)}})

    resp = post_json("/v1/chat/completions",
                     {"model": args.model,
                      "messages": [{"role": "user", "content": content}],
                      "max_tokens": args.max_tokens})
    print(resp["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
