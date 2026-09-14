#!/usr/bin/env python3
"""Generate LoRA training captions for an image (or a whole directory).

Writes a matching `.txt` next to each image (foo.png -> foo.txt), which is the
caption format draw-things-cli's `train lora --dataset` expects. Uses any
OpenAI-compatible vision chat endpoint — defaults to local Ollama.

Usage:
    caption.py <image-or-dir> [options]

Options:
    --model NAME      vision model (default: huihui_ai/qwen3-vl-abliterated:8b-instruct-q4_K_M)
    --system TEXT     system prompt: role + output-format rules (see DEFAULT_SYSTEM_PROMPT)
    --prompt TEXT     user instruction for the captioning task (see DEFAULT_PROMPT below)
    --base-url URL    OpenAI-compatible base (default: http://localhost:11434/v1 = Ollama)
    --api-key KEY     bearer token; or set OPENAI_API_KEY / OPENROUTER_API_KEY / TOGETHER_API_KEY
    --prefix TEXT     string prepended to every caption (e.g. a trigger word "ohwx, ")
    --ext .txt        caption file extension (default .txt)
    --recursive       recurse into subdirectories
    --overwrite       re-caption images that already have a caption file
    --dry-run         print captions but don't write files
    --context TEXT    a fact/correction to apply, trusted over the model's guess
    --draft TEXT      a prior caption to revise (single image)
    --revise          use each image's existing .txt as the draft to improve

Examples:
    caption.py photo.png
    caption.py ./dataset --prefix "ohwx person, " --overwrite
    caption.py ./dataset --base-url https://openrouter.ai/api/v1 --model qwen/qwen-2.5-vl-72b-instruct
    # fix a wrong caption: re-caption with a correction (and the prior draft)
    caption.py art.png --dry-run --context "the figure is a fiberglass Muffler Man statue, not a weapon"
    caption.py ./dataset --revise --context "the recurring giant is a Muffler Man statue" --overwrite
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = "huihui_ai/qwen3-vl-abliterated:8b-instruct-q4_K_M"
DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_SYSTEM_PROMPT = (
    "You are an expert image captioner producing training captions for LoRA fine-tuning. "
    "Output ONE comma-separated line with no preamble, no quotes, and no commentary. "
    "When the user supplies context or a correction, trust it over your own guess."
)
DEFAULT_PROMPT = (
    "Write a single concise training caption for this image. Describe the main subject, "
    "its appearance (hair, clothing, colors, distinctive features), pose or action, the "
    "setting, and the art/photo style."
)
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".bmp": "image/bmp", ".gif": "image/gif"}


def _api_key(arg):
    return (arg or os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("TOGETHER_API_KEY") or "")


def _clean(text):
    """Strip <think> blocks (reasoning models), surrounding quotes, and whitespace."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = text.strip().strip('"').strip("'").strip()
    return " ".join(text.split())


def build_instruction(args, draft):
    """Base prompt + optional correction context + optional prior draft to revise."""
    text = args.prompt
    if args.context:
        text += f"\n\nImportant context to apply (the user knows the subject — trust this "
        text += f"over your own guess): {args.context}"
    if draft:
        text += (f"\n\nHere is a previous draft caption. Re-examine the image and rewrite it "
                 f"into one improved caption: keep the accurate details, fix anything wrong, "
                 f"and apply the context above. Draft: \"{draft}\"")
    return text


def caption_one(path, args, draft=None):
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": args.system},
            {"role": "user", "content": [
                {"type": "text", "text": build_instruction(args, draft)},
                {"type": "image_url", "image_url": {"url": f"data:{MIME.get(ext, 'image/png')};base64,{b64}"}},
            ]},
        ],
        "stream": False,
        "temperature": 0.2,
    }
    headers = {"Content-Type": "application/json"}
    key = _api_key(args.api_key)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(args.base_url.rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        body = e.read().decode()[:300] if hasattr(e, "read") else ""
        if "refused" in str(reason).lower():
            sys.exit(f"Could not reach {args.base_url}. Is the model server running?\n"
                     f"(Ollama: `ollama serve`; or pass --base-url for another provider.)")
        sys.exit(f"API error: {reason}\n{body}".rstrip())
    cap = _clean(data["choices"][0]["message"]["content"])
    if args.prefix:
        cap = args.prefix + cap
    return cap


def gather_images(target, recursive):
    if os.path.isfile(target):
        return [target]
    out = []
    for root, _, files in os.walk(target):
        for fn in sorted(files):
            if os.path.splitext(fn)[1].lower() in IMAGE_EXTS:
                out.append(os.path.join(root, fn))
        if not recursive:
            break
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", help="image file or directory of images")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--system", default=DEFAULT_SYSTEM_PROMPT)
    p.add_argument("--prompt", default=DEFAULT_PROMPT)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--api-key")
    p.add_argument("--prefix", default="")
    p.add_argument("--ext", default=".txt")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--context", help="a fact/correction to apply (trusted over the model's "
                   "guess), e.g. \"the figure is a fiberglass Muffler Man statue, not a weapon\"")
    p.add_argument("--draft", help="a prior caption to revise (single-image refine)")
    p.add_argument("--revise", action="store_true",
                   help="use each image's existing caption file as the draft to improve")
    args = p.parse_args()

    images = gather_images(args.target, args.recursive)
    if not images:
        sys.exit(f"No images found at {args.target}")
    ext = args.ext if args.ext.startswith(".") else "." + args.ext

    done = skipped = 0
    for img in images:
        txt = os.path.splitext(img)[0] + ext
        # revising/overwriting always (re)captions; otherwise skip already-captioned
        refining = args.revise or args.draft or args.context
        if os.path.exists(txt) and not args.overwrite and not refining:
            print(f"skip (has caption): {os.path.basename(img)}")
            skipped += 1
            continue
        draft = args.draft
        if args.revise and not draft and os.path.exists(txt):
            with open(txt) as f:
                draft = f.read().strip()
        cap = caption_one(img, args, draft=draft)
        print(f"\n{os.path.basename(img)}:\n  {cap}")
        if not args.dry_run:
            with open(txt, "w") as f:
                f.write(cap)
        done += 1
    print(f"\n{'(dry-run) ' if args.dry_run else ''}captioned {done}, skipped {skipped}, total {len(images)}")


if __name__ == "__main__":
    main()
