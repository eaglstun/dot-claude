#!/usr/bin/env python3
"""HTTP fallback for the Pollinations.AI skill, for when the `polli` CLI is unavailable.

Pure standard library (urllib) — no pip dependencies — so it runs anywhere Python 3.8+
does. It mirrors the core `polli gen ...` commands against the documented HTTP API at
https://gen.pollinations.ai. Prefer the `polli` CLI when it's installed; reach for this
only as a fallback.

Auth: the API key is read ONLY from the POLLINATIONS_API_KEY environment variable — never
hardcode or commit a key. Generation needs a key; model listing does not. Get one at
https://enter.pollinations.ai, then `export POLLINATIONS_API_KEY=sk_...` (or pk_...).

Usage:
  pollinate.py image "a cat in space" -o cat.jpg [--model flux] [--width 1024] [--height 1024]
                                                 [--seed N] [--enhance] [--negative TXT]
                                                 [--transparent] [--image URL ...] [--no-tag]
  pollinate.py video "drone over mountains" -o clip.mp4 [--model ltx-2] [--duration 5]
                                                 [--aspect-ratio 16:9] [--image URL] [--no-tag]
  pollinate.py audio "Hello world" -o hello.mp3 [--voice nova] [--model elevenlabs] [--duration N]
  pollinate.py text  "summarize X" [-o out.txt] [--model openai] [--system MSG]
                                                 [--temperature N] [--seed N] [--json]
  pollinate.py models [--type image|video|audio|text]

On a 402 (insufficient balance) the chosen model is paid — retry with a free-tier model:
  image → flux / zimage   video → ltx-2   audio → elevenlabs / elevenmusic   text → openai / mistral / grok
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://gen.pollinations.ai"
FREE_HINT = {
    "image": "flux or zimage",
    "video": "ltx-2",
    "audio": "elevenlabs or elevenmusic",
    "text": "openai, mistral, or grok",
}


def die(msg: str, code: int = 1):
    print(f"pollinate: {msg}", file=sys.stderr)
    sys.exit(code)


def api_key() -> str:
    key = os.environ.get("POLLINATIONS_API_KEY")
    if not key:
        die("POLLINATIONS_API_KEY is not set. Get a key at https://enter.pollinations.ai "
            "and `export POLLINATIONS_API_KEY=sk_...`, then retry.")
    return key


def _query(params: dict) -> str:
    """Build a query string, dropping None/False and rendering True as 'true'."""
    clean = {}
    for k, v in params.items():
        if v is None or v is False:
            continue
        clean[k] = "true" if v is True else str(v)
    return urllib.parse.urlencode(clean)


def _open(url: str, *, auth: bool, timeout: int):
    # A non-default User-Agent is required — the API sits behind Cloudflare, which
    # blocks urllib's default UA signature with a 403 (error 1010).
    headers = {"User-Agent": "pollinate.py/1.0 (Pollinations skill fallback)"}
    if auth:
        headers["Authorization"] = f"Bearer {api_key()}"
    req = urllib.request.Request(url, headers=headers)
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        msg = body.strip()
        try:
            err = (json.loads(body).get("error") or {})
            msg = err.get("message") or msg
        except Exception:
            pass
        hint = ""
        if e.code == 402:
            hint = " — chosen model is paid; retry with a free-tier model."
        elif e.code == 401:
            hint = " — check that POLLINATIONS_API_KEY is valid."
        elif e.code == 403:
            hint = " — the key lacks the required scope."
        die(f"HTTP {e.code}: {msg}{hint}", code=2)
    except urllib.error.URLError as e:
        die(f"network error: {e.reason}", code=3)


def embed_metadata(path: str, prompt: str, model: str | None) -> str | None:
    """Write the prompt (and model) into the file's metadata so it travels with the file.

    Uses exiftool when available (images + video); falls back to ffmpeg for video. Returns
    the tool used, or None if neither is installed.
    """
    software = f"pollinations/{model}" if model else "pollinations"
    if shutil.which("exiftool"):
        subprocess.run(
            ["exiftool", "-overwrite_original",
             f"-Comment={prompt}", f"-Description={prompt}", f"-UserComment={prompt}",
             f"-XMP-dc:Description={prompt}", f"-Software={software}", path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return "exiftool"
    if path.lower().endswith((".mp4", ".mov")) and shutil.which("ffmpeg"):
        tmp = path + ".tagged.mp4"
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-c", "copy",
             "-metadata", f"comment={prompt}", "-metadata", f"description={prompt}", tmp],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if r.returncode == 0:
            os.replace(tmp, path)
            return "ffmpeg"
    return None


def download(endpoint: str, prompt: str, params: dict, out: str, timeout: int) -> int:
    """GET a binary generation endpoint and write it to `out`. Returns bytes written."""
    url = f"{BASE}/{endpoint}/{urllib.parse.quote(prompt, safe='')}"
    qs = _query(params)
    if qs:
        url += "?" + qs
    resp = _open(url, auth=True, timeout=timeout)
    data = resp.read()
    if not data:
        die("server returned an empty response", code=2)
    with open(out, "wb") as f:
        f.write(data)
    return len(data)


def cmd_image(a):
    params = {
        "model": a.model, "width": a.width, "height": a.height, "seed": a.seed,
        "enhance": a.enhance, "negative_prompt": a.negative, "safe": a.safe,
        "transparent": a.transparent, "quality": a.quality,
        "image": ",".join(a.image) if a.image else None,
    }
    n = download("image", a.prompt, params, a.output, a.timeout)
    tagged = None if a.no_tag else embed_metadata(a.output, a.prompt, a.model)
    print(f"saved {n:,} bytes → {a.output}" + (f"  (prompt tagged via {tagged})" if tagged else ""))


def cmd_video(a):
    params = {
        "model": a.model, "duration": a.duration, "aspectRatio": a.aspect_ratio,
        "width": a.width, "height": a.height, "seed": a.seed, "audio": a.audio,
        "enhance": a.enhance, "negative_prompt": a.negative, "image": a.image,
    }
    n = download("image", a.prompt, params, a.output, a.timeout)
    tagged = None if a.no_tag else embed_metadata(a.output, a.prompt, a.model)
    print(f"saved {n:,} bytes → {a.output}" + (f"  (prompt tagged via {tagged})" if tagged else ""))


def cmd_audio(a):
    params = {"voice": a.voice, "model": a.model, "duration": a.duration}
    n = download("audio", a.text, params, a.output, a.timeout)
    print(f"saved {n:,} bytes → {a.output}")


def cmd_text(a):
    params = {"model": a.model, "system": a.system, "temperature": a.temperature,
              "seed": a.seed, "json": a.json}
    url = f"{BASE}/text/{urllib.parse.quote(a.prompt, safe='')}"
    qs = _query(params)
    if qs:
        url += "?" + qs
    resp = _open(url, auth=True, timeout=a.timeout)
    text = resp.read().decode("utf-8", "replace")
    if a.output:
        with open(a.output, "w") as f:
            f.write(text)
        print(f"saved → {a.output}")
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")


def cmd_models(a):
    want = a.type
    if want in (None, "image", "video"):
        resp = _open(f"{BASE}/image/models", auth=False, timeout=30)
        data = json.loads(resp.read().decode("utf-8", "replace"))
        names = data if isinstance(data, list) else list(data)
        print("# image / video models")
        for m in names:
            print("  " + (m if isinstance(m, str) else json.dumps(m)))
    if want in (None, "text"):
        resp = _open(f"{BASE}/v1/models", auth=False, timeout=30)
        data = json.loads(resp.read().decode("utf-8", "replace"))
        items = data.get("data", data) if isinstance(data, dict) else data
        print("# text models")
        for m in items:
            print("  " + (m.get("id") if isinstance(m, dict) else str(m)))
    if want == "audio":
        print("# audio models are not exposed via an anonymous endpoint.")
        print("  Use `polli models --type audio`, or see references/audio.md for the voice/model list.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pollinate.py",
        description="HTTP fallback for the Pollinations skill (used when the `polli` CLI is absent).")
    sub = p.add_subparsers(dest="cmd", required=True)

    img = sub.add_parser("image", help="generate an image")
    img.add_argument("prompt")
    img.add_argument("-o", "--output", default="image.jpg")
    img.add_argument("--model", default="flux")
    img.add_argument("--width", type=int)
    img.add_argument("--height", type=int)
    img.add_argument("--seed", type=int)
    img.add_argument("--enhance", action="store_true")
    img.add_argument("--negative")
    img.add_argument("--safe", action="store_true")
    img.add_argument("--transparent", action="store_true")
    img.add_argument("--quality", choices=["low", "medium", "high", "hd"])
    img.add_argument("--image", action="append", help="reference image URL (repeatable)")
    img.add_argument("--no-tag", action="store_true", help="skip embedding the prompt in metadata")
    img.add_argument("--timeout", type=int, default=120)
    img.set_defaults(func=cmd_image)

    vid = sub.add_parser("video", help="generate a video (same path as image, video model)")
    vid.add_argument("prompt")
    vid.add_argument("-o", "--output", default="video.mp4")
    vid.add_argument("--model", default="ltx-2")
    vid.add_argument("--duration", type=int)
    vid.add_argument("--aspect-ratio", dest="aspect_ratio", choices=["16:9", "9:16"])
    vid.add_argument("--width", type=int)
    vid.add_argument("--height", type=int)
    vid.add_argument("--seed", type=int)
    vid.add_argument("--audio", action="store_true")
    vid.add_argument("--enhance", action="store_true")
    vid.add_argument("--negative")
    vid.add_argument("--image", help="reference frame URL (image-to-video)")
    vid.add_argument("--no-tag", action="store_true")
    vid.add_argument("--timeout", type=int, default=300)
    vid.set_defaults(func=cmd_video)

    aud = sub.add_parser("audio", help="text-to-speech or music")
    aud.add_argument("text")
    aud.add_argument("-o", "--output", default="speech.mp3")
    aud.add_argument("--voice", default="sage")
    aud.add_argument("--model", default="elevenlabs")
    aud.add_argument("--duration", type=int, help="seconds (music models)")
    aud.add_argument("--timeout", type=int, default=180)
    aud.set_defaults(func=cmd_audio)

    txt = sub.add_parser("text", help="one-shot text generation")
    txt.add_argument("prompt")
    txt.add_argument("-o", "--output")
    txt.add_argument("--model", default="openai")
    txt.add_argument("--system")
    txt.add_argument("--temperature", type=float)
    txt.add_argument("--seed", type=int)
    txt.add_argument("--json", action="store_true", help="force JSON-object output")
    txt.add_argument("--timeout", type=int, default=120)
    txt.set_defaults(func=cmd_text)

    mod = sub.add_parser("models", help="list available models (no key needed)")
    mod.add_argument("--type", choices=["image", "video", "audio", "text"])
    mod.set_defaults(func=cmd_models)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
