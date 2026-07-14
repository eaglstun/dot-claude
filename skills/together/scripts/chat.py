#!/usr/bin/env python3
"""Together chat completions (POST /v1/chat/completions).

Usage:
  chat.py "your prompt"  [--model deepseek-ai/DeepSeek-V3.1] [--system MSG]
                         [--max-tokens N] [--temperature F] [--json]
  chat.py --messages-file msgs.json [--model ...]   # full messages array

Prints the assistant message to stdout. Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse, json, sys
from _common import post_json

DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3.1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", help="user prompt (omit if --messages-file)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--system")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--json", action="store_true", help="request JSON-only output")
    ap.add_argument("--messages-file", help="JSON file with a full messages array")
    args = ap.parse_args()

    if args.messages_file:
        with open(args.messages_file) as f:
            messages = json.load(f)
    elif args.prompt:
        messages = []
        if args.system:
            messages.append({"role": "system", "content": args.system})
        messages.append({"role": "user", "content": args.prompt})
    else:
        ap.error("provide a prompt or --messages-file")

    payload = {
        "model": args.model,
        "messages": messages,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }
    if args.json:
        payload["response_format"] = {"type": "json_object"}

    resp = post_json("/v1/chat/completions", payload)
    print(resp["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
