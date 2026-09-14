#!/usr/bin/env python3
"""Train a LoRA with draw-things-cli — a thin wrapper that validates the dataset,
builds the command, streams training output, and reports the resulting .ckpt.

Usage:
    train_lora.py --dataset DIR --output NAME [options]

Required:
    --dataset DIR     directory of images (+ matching .txt captions; see caption.py)
    --output NAME     output LoRA filename prefix (lands in the models dir as NAME...ckpt)

Common options (passed through to `draw-things-cli train lora`):
    --model NAME      base model (default: sd_v1.5_f16.ckpt). FLUX training: see note below.
    --steps N         training steps (default 500)
    --rank N          LoRA rank (default 16)
    --scale F         LoRA scale (default 1.0)
    --learning-rate L UNet LR; float or range like 5e-5:1e-4 (default 1e-4)
    --resolution N    square training resolution (default 512)
    --save-every N    checkpoint every N steps, 0 = final only (default 0)
    --name TEXT       display name in LoRA metadata (default: --output value)
    --seed N
    --resume PATH     resume from a checkpoint
    --dry-run         validate + print resolved config without training
    --cli PATH        path to draw-things-cli (default: auto-detect)
    --                everything after `--` is forwarded verbatim to the CLI
                      (e.g. -- --caption-dropout 0.1 --cotrain-text-model)

Note: upstream issue #81 reports FLUX.1 [dev] LoRA training may save only the init
state. SD-family training is the safer bet until that's confirmed fixed.
"""

import argparse
import os
import shutil
import subprocess
import sys

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def find_cli(explicit):
    if explicit:
        return explicit
    found = shutil.which("draw-things-cli") or "/opt/homebrew/bin/draw-things-cli"
    if not os.path.exists(found):
        sys.exit("draw-things-cli not found. Install: brew tap drawthingsai/draw-things "
                 "&& brew install draw-things-cli  (or pass --cli PATH)")
    return found


def check_dataset(d):
    if not os.path.isdir(d):
        sys.exit(f"--dataset is not a directory: {d}")
    imgs = [f for f in os.listdir(d) if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
    if not imgs:
        sys.exit(f"No images found in {d}")
    missing = [f for f in imgs if not os.path.exists(os.path.join(d, os.path.splitext(f)[0] + ".txt"))]
    print(f"dataset: {len(imgs)} image(s), {len(imgs) - len(missing)} with captions", flush=True)
    if missing:
        print(f"  ⚠ {len(missing)} image(s) have no .txt caption "
              f"(e.g. {missing[0]}). Run caption.py first, or train uncaptioned.", flush=True)
    return len(imgs)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--model", default="sd_v1.5_f16.ckpt")
    p.add_argument("--steps", default="500")
    p.add_argument("--rank", default="16")
    p.add_argument("--scale", default="1.0")
    p.add_argument("--learning-rate", default="1e-4")
    p.add_argument("--resolution", default="512")
    p.add_argument("--save-every", default="0")
    p.add_argument("--name")
    p.add_argument("--seed")
    p.add_argument("--resume")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--cli")
    p.add_argument("passthrough", nargs="*", help="args after -- go straight to the CLI")
    args = p.parse_args()

    cli = find_cli(args.cli)
    check_dataset(args.dataset)

    cmd = [cli, "train", "lora",
           "--model", args.model, "--dataset", args.dataset, "--output", args.output,
           "--steps", str(args.steps), "--rank", str(args.rank), "--scale", str(args.scale),
           "--learning-rate", str(args.learning_rate), "--resolution", str(args.resolution),
           "--save-every", str(args.save_every), "--name", args.name or args.output]
    if args.seed:
        cmd += ["--seed", str(args.seed)]
    if args.resume:
        cmd += ["--resume", args.resume]
    if args.dry_run:
        cmd += ["--dry-run"]
    # forward anything after `--`
    extra = args.passthrough
    if extra and extra[0] == "--":
        extra = extra[1:]
    cmd += extra

    print("running:", " ".join(cmd), "\n", flush=True)
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        sys.exit(f"\ntraining failed (exit {rc})")
    if not args.dry_run:
        models = os.environ.get("DRAWTHINGS_MODELS_DIR") or os.path.expanduser(
            "~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models")
        hits = sorted(f for f in os.listdir(models) if f.startswith(args.output) and f.endswith(".ckpt")) \
            if os.path.isdir(models) else []
        print("\ndone. LoRA file(s) in models dir:")
        for h in hits:
            print("  ", h)
        print("Select it in the app, or use it in draw-things-cli generate via --config-json loras.")


if __name__ == "__main__":
    main()
