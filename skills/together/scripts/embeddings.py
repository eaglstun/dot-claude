#!/usr/bin/env python3
"""Together embeddings (POST /v1/embeddings).

Only one embedding model is serverless on Together (the default below).

Usage:
  embeddings.py "a single string"
  embeddings.py "first" "second" "third"          # multiple inputs
  embeddings.py --input-file lines.json            # JSON array of strings
      [--model intfloat/multilingual-e5-large-instruct] [--out vecs.json]

Prints embeddings as JSON to stdout (or --out file). One float array per input
at .data[].embedding. Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse, json, sys
from _common import post_json

DEFAULT_MODEL = "intfloat/multilingual-e5-large-instruct"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="*", help="one or more strings to embed")
    ap.add_argument("--input-file", help="JSON file with an array of strings")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out", help="write embeddings JSON here instead of stdout")
    args = ap.parse_args()

    if args.input_file:
        with open(args.input_file) as f:
            inputs = json.load(f)
    elif args.inputs:
        inputs = args.inputs
    else:
        ap.error("provide one or more strings or --input-file")

    resp = post_json("/v1/embeddings",
                     {"model": args.model,
                      "input": inputs[0] if len(inputs) == 1 else inputs})
    vectors = [d["embedding"] for d in resp["data"]]
    out = json.dumps(vectors)
    if args.out:
        with open(args.out, "w") as f:
            f.write(out)
        print(f"wrote {len(vectors)} embedding(s) ({len(vectors[0])} dim) to {args.out}",
              file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
