#!/usr/bin/env python3
"""Shared plumbing for the Together AI skill scripts.

Pure standard library (urllib/ssl/socket) — no pip dependencies — so the scripts
run anywhere Python 3.8+ does. Not meant to be invoked directly; the per-endpoint
scripts in this directory import from it.

Auth: the API key is read ONLY from the TOGETHER_API_KEY environment variable —
never hardcode or commit a key.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid

BASE = "https://api.together.ai"

# Together's API sits behind Cloudflare, which 403s (error 1010) requests carrying
# the default "Python-urllib/x.y" User-Agent. Send a browser UA so every request
# (set centrally in _send) is allowed through.
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def api_key() -> str:
    key = os.environ.get("TOGETHER_API_KEY")
    if not key:
        die("TOGETHER_API_KEY is not set in the environment. "
            "export TOGETHER_API_KEY=... and retry.")
    return key


def die(msg: str, code: int = 1):
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _send(req: urllib.request.Request, raw: bool):
    req.add_header("User-Agent", USER_AGENT)  # clear Cloudflare (see USER_AGENT)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        die(f"HTTP {e.code} from {req.full_url}\n{detail}")
    except urllib.error.URLError as e:
        die(f"could not reach {req.full_url}: {e.reason}")
    return body if raw else json.loads(body)


def post_json(path: str, payload: dict, raw: bool = False):
    """POST a JSON body. Returns parsed JSON, or raw bytes if raw=True."""
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    return _send(req, raw)


def get_json(path: str):
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {api_key()}"},
        method="GET",
    )
    return _send(req, raw=False)


def post_multipart(path: str, fields: dict, file_field: str = None,
                   file_path: str = None):
    """POST multipart/form-data. `fields` are plain form fields; if file_path is
    a local file it's uploaded under file_field, if it's an http(s) URL it's sent
    as a plain field value instead (the API accepts a URL there)."""
    boundary = "----togetherboundary" + uuid.uuid4().hex
    parts = []

    def add_field(name, value):
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    for k, v in fields.items():
        if v is not None:
            add_field(k, v)

    if file_path is not None:
        if file_path.startswith(("http://", "https://")):
            add_field(file_field, file_path)
        else:
            with open(file_path, "rb") as f:
                data = f.read()
            fname = os.path.basename(file_path)
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{fname}"\r\n'.encode())
            parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
            parts.append(data)
            parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        BASE + path,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    return _send(req, raw=False)


# ---- provenance embedding (mirrors references/provenance.md) ----------------

def embed_image_meta(path: str, model: str, prompt: str):
    """Embed model + prompt into an image/video via exiftool (in place)."""
    if not shutil.which("exiftool"):
        print("warn: exiftool not found; skipping provenance embed "
              "(brew install exiftool)", file=sys.stderr)
        return
    subprocess.run(
        ["exiftool", "-overwrite_original",
         f"-Comment={prompt}", f"-Description={prompt}",
         f"-UserComment={prompt}", f"-XMP-dc:Description={prompt}",
         f"-Software=together/{model}", path],
        check=False, capture_output=True)


def embed_audio_meta(path: str, model: str, prompt: str):
    """Embed model + prompt into an audio file via ffmpeg (remux to temp)."""
    if not shutil.which("ffmpeg"):
        print("warn: ffmpeg not found; skipping provenance embed",
              file=sys.stderr)
        return
    root, ext = os.path.splitext(path)
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False).name
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", path,
         "-metadata", f"comment=model=together/{model}; prompt={prompt}",
         "-c", "copy", tmp],
        check=False, capture_output=True)
    if r.returncode == 0:
        shutil.move(tmp, path)
    else:
        os.unlink(tmp)
        print("warn: ffmpeg metadata embed failed; left file untouched",
              file=sys.stderr)
