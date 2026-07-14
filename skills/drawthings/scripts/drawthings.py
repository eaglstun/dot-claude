#!/usr/bin/env python3
"""Call the local Draw Things HTTP API (AUTOMATIC1111-compatible) and save images to disk.

Usage:
    drawthings.py config [--url URL]
    drawthings.py txt2img "<prompt>" -o out.png [options]
    drawthings.py img2img "<prompt>" --init in.png -o out.png [options]

Options (txt2img / img2img):
    -o, --output PATH     output file (default: drawthings.png). With --batch >1,
                          a "-N" index is appended before the extension.
    --negative TEXT       negative prompt
    --width N             image width
    --height N            image height
    --steps N             sampling steps
    --guidance F          guidance / CFG scale (Draw Things calls this guidance_scale)
    --sampler NAME        sampler name (e.g. "DPM++ 2M Karras")
    --seed N              seed (default: random/-1)
    --model NAME          model file to use (otherwise the app's current model)
    --batch N             number of images (default 1)
    --lora FILE[:W]       LoRA .ckpt to apply, optional :weight (default 1.0).
                          Repeatable. UNLIKE other options, LoRAs do NOT inherit
                          from the UI: with no --lora the request clears them
                          (no LoRA); passing --lora sets exactly those, replacing
                          whatever is selected in the app.
    --control FILE[:W]    ControlNet/adapter .ckpt to apply, optional :weight
                          (repeatable). Structural controls (depth/pose) read their
                          guide from --init (img2img); reference/identity controls
                          (PuLID) read it from --control-image (txt2img).
    --control-importance  balanced (default) | prompt | control
    --control-image PATH  reference image on the control entry (PuLID etc.), txt2img
    --url URL             API base URL (default http://127.0.0.1:7860)

img2img only:
    --init PATH           initial image (required)
    --strength F          denoising strength 0..1 (default 0.75)

Notes:
    * Any parameter you DON'T pass is inherited from whatever is currently
      selected in the Draw Things UI — the API overrides, it does not reset.
      EXCEPTION: LoRAs default to none (cleared) unless you pass --lora, so a
      LoRA left selected in the app can't silently ride along on every call.
    * The API server must be enabled in the app:
      Settings -> Advanced -> API Server, Protocol HTTP, Port 7860.
    * Saved file paths are printed to stdout, one per line.
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:7860"
CONNECT_HINT = (
    "Could not reach the Draw Things API at {url}.\n"
    "Open the Draw Things app and enable: Settings -> Advanced -> API Server\n"
    "(Protocol HTTP, Port 7860, IP localhost). For LAN access set IP to 0.0.0.0\n"
    "and point --url at the Mac's address (e.g. http://<your-mac-lan-ip>:7860)."
)


def _request(url, payload=None, method="GET", timeout=600):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, (ConnectionRefusedError, TimeoutError)) or "refused" in str(reason).lower():
            sys.exit(CONNECT_HINT.format(url=url))
        body = ""
        if hasattr(e, "read"):
            try:
                body = e.read().decode()
            except Exception:
                pass
        sys.exit(f"API error from {url}: {reason}\n{body}".rstrip())


def _decode_image(b64):
    """Draw Things returns raw base64; some A1111 builds prefix a data URI."""
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)


def _embed_metadata(path, prompt, model):
    """Embed the prompt + model into the file so it travels with the image."""
    if not shutil.which("exiftool"):
        return
    software = f"drawthings/{model}" if model else "drawthings"
    subprocess.run(
        [
            "exiftool", "-overwrite_original",
            f"-Comment={prompt}", f"-Description={prompt}",
            f"-UserComment={prompt}", f"-XMP-dc:Description={prompt}",
            f"-Software={software}", path,
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )


def _save_images(images, output, prompt, model):
    base, ext = os.path.splitext(output)
    ext = ext or ".png"
    saved = []
    for i, b64 in enumerate(images):
        path = output if len(images) == 1 else f"{base}-{i + 1}{ext}"
        with open(path, "wb") as f:
            f.write(_decode_image(b64))
        _embed_metadata(path, prompt, model)
        saved.append(path)
    return saved


def _control_struct(spec, importance, image_b64=None):
    """Build a full Draw Things control entry. The API decodes controls strictly —
    every key must be present or it returns 422. spec is FILE or FILE:WEIGHT.
    image_b64 attaches a per-control reference image (for identity/reference adapters
    like PuLID, which read the reference here rather than from init_images)."""
    file, _, w = spec.partition(":")
    control = {
        "file": file,
        "weight": float(w) if w else 1.0,
        "guidanceStart": 0.0,
        "guidanceEnd": 1.0,
        "noPrompt": False,
        "inputOverride": "",
        "controlImportance": importance,
        "targetBlocks": [],
        "downSamplingRate": 0.0,
        "globalAveragePooling": False,
    }
    if image_b64:
        control["image"] = image_b64
    return control


def _build_payload(args):
    payload = {"prompt": args.prompt}
    optional = {
        "negative_prompt": args.negative,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "guidance_scale": args.guidance,
        "sampler": args.sampler,
        "seed": args.seed,
        "model": args.model,
        "batch_count": args.batch if args.batch and args.batch > 1 else None,
    }
    payload.update({k: v for k, v in optional.items() if v is not None})
    # LoRAs are the one field that does NOT inherit from the UI: default to none
    # (send an empty list to clear any LoRA selected in the app), opt in with --lora.
    # This avoids an invisible UI-selected LoRA riding along on every generation.
    loras = []
    for spec in getattr(args, "lora", None) or []:
        file, _, w = spec.partition(":")
        loras.append({"file": file, "weight": float(w) if w else 1.0, "mode": "all"})
    payload["loras"] = loras
    if getattr(args, "control", None):
        cimg = None
        if getattr(args, "control_image", None):
            with open(args.control_image, "rb") as f:
                cimg = base64.b64encode(f.read()).decode()
        payload["controls"] = [_control_struct(c, args.control_importance, cimg) for c in args.control]
    return payload


def cmd_config(args):
    print(json.dumps(_request(args.url.rstrip("/") + "/", method="GET"), indent=2))


def cmd_txt2img(args):
    payload = _build_payload(args)
    resp = _request(args.url.rstrip("/") + "/sdapi/v1/txt2img", payload, method="POST")
    images = resp.get("images") or []
    if not images:
        sys.exit(f"No images returned. Response: {json.dumps(resp)[:500]}")
    for p in _save_images(images, args.output, args.prompt, args.model):
        print(p)


def cmd_img2img(args):
    if not args.init:
        sys.exit("img2img requires --init <image>")
    payload = _build_payload(args)
    with open(args.init, "rb") as f:
        payload["init_images"] = [base64.b64encode(f.read()).decode()]
    if args.strength is not None:
        payload["strength"] = args.strength
    resp = _request(args.url.rstrip("/") + "/sdapi/v1/img2img", payload, method="POST")
    images = resp.get("images") or []
    if not images:
        sys.exit(f"No images returned. Response: {json.dumps(resp)[:500]}")
    for p in _save_images(images, args.output, args.prompt, args.model):
        print(p)


def _add_gen_args(p):
    p.add_argument("prompt")
    p.add_argument("-o", "--output", default="drawthings.png")
    p.add_argument("--negative")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--guidance", type=float)
    p.add_argument("--sampler")
    p.add_argument("--seed", type=int, default=-1)
    p.add_argument("--model")
    p.add_argument("--batch", type=int)
    p.add_argument("--lora", action="append", metavar="FILE[:WEIGHT]",
                   help="LoRA .ckpt to apply, optional :weight (default 1.0). "
                        "Repeatable. LoRAs do NOT inherit from the UI: omit for no "
                        "LoRA (cleared); passing this replaces any UI selection.")
    p.add_argument("--control", action="append", metavar="FILE[:WEIGHT]",
                   help="ControlNet/adapter .ckpt to apply (repeatable). Structural "
                        "controls read --init (img2img); identity controls read "
                        "--control-image (txt2img).")
    p.add_argument("--control-importance", default="balanced",
                   help="balanced (default) | prompt | control")
    p.add_argument("--control-image", metavar="PATH",
                   help="reference image attached to the control entry itself (for "
                        "identity/reference adapters like PuLID). Use on txt2img.")
    p.add_argument("--url", default=DEFAULT_URL)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("config", help="GET / — dump the app's current configuration")
    pc.add_argument("--url", default=DEFAULT_URL)
    pc.set_defaults(func=cmd_config)

    pt = sub.add_parser("txt2img", help="generate from a text prompt")
    _add_gen_args(pt)
    pt.set_defaults(func=cmd_txt2img)

    pi = sub.add_parser("img2img", help="generate from an init image + prompt")
    _add_gen_args(pi)
    pi.add_argument("--init", help="initial image (required)")
    pi.add_argument("--strength", type=float)
    pi.set_defaults(func=cmd_img2img)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
