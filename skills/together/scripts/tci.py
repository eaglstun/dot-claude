#!/usr/bin/env python3
"""Together Code Interpreter (POST /v1/tci/execute).

Runs Python in a hosted sandbox and prints captured outputs. Pass --session-id to
reuse a kernel (variables/imports/files persist); omit it to start fresh (the new
id is printed to stderr).

Usage:
  tci.py "import numpy as np; print(np.arange(5).sum())"
  tci.py --code-file script.py [--session-id ses_abc123]
  tci.py "print(open('data.csv').read())" --upload data.csv   # drop a file in first

Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse, base64, os, sys
from _common import post_json, die


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code", nargs="?", help="Python code (or use --code-file)")
    ap.add_argument("--code-file", help="read code from this file")
    ap.add_argument("--session-id", help="reuse an existing session")
    ap.add_argument("--upload", action="append", default=[],
                    help="local file to place in the sandbox (repeatable)")
    args = ap.parse_args()

    if args.code_file:
        with open(args.code_file) as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        ap.error("provide code or --code-file")

    payload = {"language": "python", "code": code}
    if args.session_id:
        payload["session_id"] = args.session_id
    if args.upload:
        files = []
        for p in args.upload:
            with open(p, "rb") as f:
                data = f.read()
            try:
                files.append({"name": os.path.basename(p), "encoding": "string",
                              "content": data.decode("utf-8")})
            except UnicodeDecodeError:
                files.append({"name": os.path.basename(p), "encoding": "base64",
                              "content": base64.b64encode(data).decode()})
        payload["files"] = files

    resp = post_json("/v1/tci/execute", payload)
    if resp.get("errors"):
        die(str(resp["errors"]))
    data = resp["data"]
    print(f"session: {data.get('session_id')}  status: {data.get('status')}",
          file=sys.stderr)
    for out in data.get("outputs", []):
        t = out.get("type")
        d = out.get("data")
        if t in ("stdout", "stderr", "error"):
            sys.stderr.write(d) if t != "stdout" else sys.stdout.write(d)
        else:  # execute_result / display_data -> MIME object
            print(f"[{t}] {d}")


if __name__ == "__main__":
    main()
