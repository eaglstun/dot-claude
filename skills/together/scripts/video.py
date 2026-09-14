#!/usr/bin/env python3
"""Together video generation (async): submit -> poll -> download.

POSTs to /v2/videos (note: v2, not v1), polls GET /v2/videos/{id} until the job
is completed, downloads outputs.video_url, and embeds model+prompt provenance.

Usage:
  video.py "a neon koi swimming through fog" -o koi.mp4
      [--model ByteDance/Seedance-1.0-lite] [--seconds 5] [--ratio 16:9]
      [--seed N] [--steps N] [--poll 5] [--timeout 900]

Auth via TOGETHER_API_KEY env var.
"""
from __future__ import annotations
import argparse, sys, time, urllib.request
from _common import post_json, get_json, embed_image_meta, die

DEFAULT_MODEL = "ByteDance/Seedance-1.0-lite"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("-o", "--out", required=True, help="output mp4 path")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--seconds", default="5")
    ap.add_argument("--ratio", default=None)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--steps", type=int)
    ap.add_argument("--poll", type=float, default=5.0, help="seconds between polls")
    ap.add_argument("--timeout", type=float, default=900.0)
    args = ap.parse_args()

    payload = {"model": args.model, "prompt": args.prompt,
               "seconds": str(args.seconds)}
    if args.ratio:
        payload["ratio"] = args.ratio
    for k in ("seed", "steps"):
        v = getattr(args, k)
        if v is not None:
            payload[k] = v

    job = post_json("/v2/videos", payload)
    job_id = job["id"]
    print(f"submitted job {job_id} (status={job.get('status')})", file=sys.stderr)

    waited = 0.0
    while True:
        if waited >= args.timeout:
            die(f"timed out after {args.timeout}s; job {job_id} still pending")
        time.sleep(args.poll)
        waited += args.poll
        job = get_json(f"/v2/videos/{job_id}")
        status = job.get("status")
        print(f"  [{int(waited)}s] status={status}", file=sys.stderr)
        if status == "completed":
            break
        if status == "failed":
            die(f"job failed: {job.get('error')}")

    url = job.get("outputs", {}).get("video_url")
    if not url:
        die(f"completed but no video_url: {job}")
    urllib.request.urlretrieve(url, args.out)
    embed_image_meta(args.out, args.model, args.prompt)
    cost = job.get("outputs", {}).get("cost")
    print(f"{args.out}  (cost={cost})" if cost is not None else args.out)


if __name__ == "__main__":
    main()
