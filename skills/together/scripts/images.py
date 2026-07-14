#!/usr/bin/env python3
"""Together image generation (POST /v1/images/generations).

Usage:
  images.py "a neon koi in fog" -o koi.png
      [--model black-forest-labs/FLUX.1-schnell] [--width 1024] [--height 1024]
      [--steps N] [--seed N] [--image-url URL]   # image-url for edit models

Saves the image to -o and embeds model+prompt provenance (exiftool).
Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse, base64, sys, urllib.request
from _common import post_json, embed_image_meta, die

DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("-o", "--out", required=True, help="output image path")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--steps", type=int)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--image-url", help="input image for edit-capable models")
    args = ap.parse_args()

    payload = {"model": args.model, "prompt": args.prompt,
               "width": args.width, "height": args.height,
               "response_format": "url"}
    for k in ("steps", "seed"):
        v = getattr(args, k)
        if v is not None:
            payload[k] = v
    if args.image_url:
        payload["image_url"] = args.image_url

    resp = post_json("/v1/images/generations", payload)
    item = resp["data"][0]
    if item.get("url"):
        urllib.request.urlretrieve(item["url"], args.out)
    elif item.get("b64_json"):
        with open(args.out, "wb") as f:
            f.write(base64.b64decode(item["b64_json"]))
    else:
        die(f"no url or b64_json in response: {item}")

    embed_image_meta(args.out, args.model, args.prompt)
    print(args.out)


if __name__ == "__main__":
    main()
