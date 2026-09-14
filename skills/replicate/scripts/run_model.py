#!/usr/bin/env python3
"""Run a Replicate model and save file outputs to disk.

Usage:
    run_model.py <owner/name>[:version] --input '<json>' [--output DIR] [--basename NAME]
    run_model.py <owner/name> --input-file input.json --output DIR

Environment:
    REPLICATE_API_TOKEN  (required)

Input values that are local file paths are auto-uploaded as file handles.
Values that look like URLs (http/https/data) are passed through.

Output:
    Saved file paths are printed to stdout, one per line.
    Progress and errors go to stderr.

By default, every run also writes a sidecar `<basename>.meta.json` capturing
the model, inputs, timestamps, and (when available) the Replicate prediction
id. Compact metadata is also embedded into common media formats (PNG tEXt,
JPEG/WebP EXIF, MP4/WebM via ffmpeg, WAV/MP3 via mutagen if installed).

Flags:
  --no-metadata   Disable both sidecar AND embedding (raw outputs only).
  --no-sidecar    Skip the .meta.json sidecar but still embed metadata in
                  the output files. Useful when you want prompts traveling
                  with each output but no separate JSON sidecars.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse


# --- output saving helpers (unchanged) ---------------------------------------

def _url_of(item) -> str | None:
    for attr in ("url", "href"):
        v = getattr(item, attr, None)
        if v:
            return v
    s = str(item)
    return s if s.startswith(("http://", "https://")) else None


def _ext_from_url(url: str) -> str:
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    return ext or ".bin"


def save_output(item, out_dir: pathlib.Path, basename: str, suffix: str = "") -> pathlib.Path:
    """Save one output item. Returns the saved path."""
    # FileOutput-like: has .read() that returns bytes
    if hasattr(item, "read") and callable(item.read):
        url = _url_of(item) or ""
        ext = _ext_from_url(url) if url else ".bin"
        path = out_dir / f"{basename}{suffix}{ext}"
        data = item.read()
        with open(path, "wb") as f:
            f.write(data if isinstance(data, (bytes, bytearray)) else data.encode())
        return path

    # Plain URL string
    if isinstance(item, str) and item.startswith(("http://", "https://")):
        ext = _ext_from_url(item)
        path = out_dir / f"{basename}{suffix}{ext}"
        req = urllib.request.Request(item)
        token = os.environ.get("REPLICATE_API_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req) as r, open(path, "wb") as f:
            f.write(r.read())
        return path

    # Fallback: treat as text
    path = out_dir / f"{basename}{suffix}.txt"
    with open(path, "w") as f:
        f.write(str(item))
    return path


def save_output_tree(item, out_dir: pathlib.Path, basename: str, suffix: str = "") -> list[pathlib.Path]:
    """Recursively save nested output structures (list/dict/leaf).

    Handles outputs like SAM2's ``{"combined_mask": FileOutput, "individual_masks": [FileOutput, ...]}``
    where a dict value is itself a list of file-like items. Returns all saved paths in order.
    """
    if isinstance(item, list):
        paths: list[pathlib.Path] = []
        for i, sub in enumerate(item):
            paths.extend(save_output_tree(sub, out_dir, basename, suffix=f"{suffix}_{i}"))
        return paths
    if isinstance(item, dict):
        paths = []
        for key, value in item.items():
            paths.extend(save_output_tree(value, out_dir, basename, suffix=f"{suffix}_{key}"))
        return paths
    return [save_output(item, out_dir, basename, suffix=suffix)]


def prepare_inputs(input_data: dict) -> dict:
    """Open local file paths as file handles for upload."""
    prepared = {}
    for k, v in input_data.items():
        if isinstance(v, str) and not v.startswith(("http://", "https://", "data:")) and os.path.isfile(v):
            prepared[k] = open(v, "rb")
        else:
            prepared[k] = v
    return prepared


# --- metadata: sidecar + embedding -------------------------------------------

_FFMPEG_CACHED: bool | None = None


def _ffmpeg_available() -> bool:
    global _FFMPEG_CACHED
    if _FFMPEG_CACHED is not None:
        return _FFMPEG_CACHED
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        _FFMPEG_CACHED = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        _FFMPEG_CACHED = False
    return _FFMPEG_CACHED


def _compact_metadata(
    model_slug: str,
    original_inputs: dict,
    version: str | None = None,
    prediction_id: str | None = None,
    runtime_seconds: float | None = None,
) -> dict:
    """Blob for embedding inside the file itself.

    Includes everything needed to reproduce the run: model slug, resolved
    version hash, Replicate prediction id, runtime, and the full user-typed
    input dict. ``prompt`` is surfaced at top-level too so format-specific
    embedders (EXIF ImageDescription, ID3 TIT2) can use it directly.
    """
    compact: dict = {"model": model_slug, "tool": "replicate-skill"}
    if version:
        compact["version"] = version
    if prediction_id:
        compact["prediction_id"] = prediction_id
    if runtime_seconds is not None:
        compact["runtime_seconds"] = round(runtime_seconds, 3)
    if isinstance(original_inputs, dict):
        compact["inputs"] = original_inputs
        p = original_inputs.get("prompt")
        if isinstance(p, str):
            compact["prompt"] = p
    return compact


def _embed_png(path: pathlib.Path, model_slug: str, compact: dict) -> None:
    from PIL import Image, PngImagePlugin  # type: ignore
    with Image.open(path) as im:
        im.load()
        pnginfo = PngImagePlugin.PngInfo()
        # Preserve any existing text chunks.
        existing = getattr(im, "text", {}) or {}
        for k, v in existing.items():
            if k not in ("Software", "Source", "Comment"):
                pnginfo.add_text(k, str(v))
        pnginfo.add_text("Software", "replicate-skill")
        pnginfo.add_text("Source", model_slug)
        pnginfo.add_text("Comment", json.dumps(compact, separators=(",", ":")))
        im.save(path, format="PNG", pnginfo=pnginfo)


def _embed_exif_image(path: pathlib.Path, fmt: str, model_slug: str, compact: dict, prompt: str | None) -> None:
    from PIL import Image  # type: ignore
    blob = json.dumps(compact, separators=(",", ":"))
    with Image.open(path) as im:
        im.load()
        try:
            exif = im.getexif()
        except Exception:
            exif = Image.Exif()  # type: ignore[attr-defined]
        # UserComment (0x9286) — pragmatic ASCII-prefixed UTF-8.
        exif[0x9286] = b"ASCII\x00\x00\x00" + blob.encode("utf-8", errors="replace")
        if prompt:
            try:
                exif[0x010E] = prompt  # ImageDescription
            except Exception:
                pass
        save_kwargs = {"exif": exif.tobytes()}
        if fmt.upper() == "JPEG":
            save_kwargs["quality"] = "keep"
        im.save(path, format=fmt, **save_kwargs)


def _embed_video_ffmpeg(path: pathlib.Path, model_slug: str, compact: dict) -> None:
    if not _ffmpeg_available():
        print(f"[metadata] ffmpeg not on PATH, skipping video metadata for {path.name}", file=sys.stderr)
        return
    blob = json.dumps(compact, separators=(",", ":"))
    # Preserve original extension so ffmpeg can infer output format (e.g.
    # ".mp4" not ".mp4.tmp" — the latter breaks muxer selection).
    tmp = path.with_name(f".{path.stem}.meta-tmp{path.suffix}")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(path),
        "-codec", "copy",
        "-metadata", f"comment={blob}",
        "-metadata", f"title={model_slug}",
        str(tmp),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace").strip()
        print(f"[metadata] ffmpeg failed for {path.name}: {err}", file=sys.stderr)
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return
    os.replace(tmp, path)


def _embed_audio_mutagen(path: pathlib.Path, kind: str, model_slug: str, compact: dict) -> None:
    try:
        import mutagen  # type: ignore  # noqa: F401
    except ImportError:
        print(f"[metadata] mutagen not installed, skipping audio metadata for {path.name}", file=sys.stderr)
        return
    blob = json.dumps(compact, separators=(",", ":"))
    if kind == "mp3":
        from mutagen.id3 import ID3, ID3NoHeaderError, TXXX, TIT2  # type: ignore
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()
        tags.add(TXXX(encoding=3, desc="model", text=model_slug))
        if "prompt" in compact:
            tags.add(TXXX(encoding=3, desc="prompt", text=compact["prompt"]))
            tags.add(TIT2(encoding=3, text=compact["prompt"][:120]))
        tags.add(TXXX(encoding=3, desc="metadata_json", text=blob))
        tags.save(path)
    elif kind == "wav":
        from mutagen.wave import WAVE  # type: ignore
        from mutagen.id3 import TXXX  # type: ignore
        w = WAVE(path)
        if w.tags is None:
            w.add_tags()
        w.tags.add(TXXX(encoding=3, desc="model", text=model_slug))
        if "prompt" in compact:
            w.tags.add(TXXX(encoding=3, desc="prompt", text=compact["prompt"]))
        w.tags.add(TXXX(encoding=3, desc="metadata_json", text=blob))
        w.save()


def embed_metadata(
    path: pathlib.Path,
    model_slug: str,
    original_inputs: dict,
    version: str | None = None,
    prediction_id: str | None = None,
    runtime_seconds: float | None = None,
) -> None:
    """Try to embed compact metadata into `path` based on extension.

    Any failure is logged to stderr but does not raise.
    """
    ext = path.suffix.lower()
    compact = _compact_metadata(
        model_slug,
        original_inputs,
        version=version,
        prediction_id=prediction_id,
        runtime_seconds=runtime_seconds,
    )
    prompt = compact.get("prompt") if isinstance(compact.get("prompt"), str) else None
    try:
        if ext == ".png":
            try:
                _embed_png(path, model_slug, compact)
            except ImportError:
                print(f"[metadata] Pillow not installed, skipping PNG metadata for {path.name}", file=sys.stderr)
            except Exception as e:
                print(f"[metadata] PNG embed failed for {path.name}: {type(e).__name__}: {e}", file=sys.stderr)
        elif ext in (".jpg", ".jpeg"):
            try:
                _embed_exif_image(path, "JPEG", model_slug, compact, prompt)
            except ImportError:
                print(f"[metadata] Pillow not installed, skipping JPEG metadata for {path.name}", file=sys.stderr)
            except Exception as e:
                print(f"[metadata] JPEG embed failed for {path.name}: {type(e).__name__}: {e}", file=sys.stderr)
        elif ext == ".webp":
            try:
                _embed_exif_image(path, "WEBP", model_slug, compact, prompt)
            except ImportError:
                print(f"[metadata] Pillow not installed, skipping WebP metadata for {path.name}", file=sys.stderr)
            except Exception as e:
                print(f"[metadata] WebP embed failed for {path.name}: {type(e).__name__}: {e}", file=sys.stderr)
        elif ext in (".mp4", ".webm", ".mov", ".m4v", ".mkv"):
            try:
                _embed_video_ffmpeg(path, model_slug, compact)
            except Exception as e:
                print(f"[metadata] video embed failed for {path.name}: {type(e).__name__}: {e}", file=sys.stderr)
        elif ext == ".mp3":
            try:
                _embed_audio_mutagen(path, "mp3", model_slug, compact)
            except Exception as e:
                print(f"[metadata] MP3 embed failed for {path.name}: {type(e).__name__}: {e}", file=sys.stderr)
        elif ext == ".wav":
            try:
                _embed_audio_mutagen(path, "wav", model_slug, compact)
            except Exception as e:
                print(f"[metadata] WAV embed failed for {path.name}: {type(e).__name__}: {e}", file=sys.stderr)
        # other extensions: sidecar only
    except Exception as e:  # defensive outer guard
        print(f"[metadata] unexpected embed error for {path.name}: {type(e).__name__}: {e}", file=sys.stderr)


def write_sidecar(
    out_dir: pathlib.Path,
    basename: str,
    model_slug: str,
    version: str | None,
    prediction_id: str | None,
    created_at: str,
    completed_at: str,
    runtime_seconds: float,
    original_inputs: dict,
    saved_paths: list[pathlib.Path],
) -> pathlib.Path | None:
    sidecar = out_dir / f"{basename}.meta.json"
    payload = {
        "model": model_slug,
        "version": version,
        "prediction_id": prediction_id,
        "created_at": created_at,
        "completed_at": completed_at,
        "runtime_seconds": round(runtime_seconds, 3),
        "inputs": original_inputs,
        "output_files": [p.name for p in saved_paths] + [sidecar.name],
    }
    try:
        with open(sidecar, "w") as f:
            json.dump(payload, f, indent=2, default=str)
            f.write("\n")
        return sidecar
    except OSError as e:
        print(f"[metadata] WARNING: failed to write sidecar {sidecar}: {e}", file=sys.stderr)
        return None


# --- Replicate run with prediction id ----------------------------------------

def _resolve_latest_version(client, owner: str, name: str) -> str | None:
    """Look up the latest version id for owner/name. Returns None on failure.

    Several older community models on Replicate (andreasjansson/illusion,
    bytedance/bagel, fofr/latent-consistency-model, jagilley/controlnet-scribble,
    lucataco/flux-dev-multi-lora, fermatresearch/magic-image-refiner, meta/sam-2,
    ...) 404 on the bare-slug predictions path because there's no "latest"
    alias. Pinning to the resolved latest-version hash avoids the 404 and also
    gives us reproducible runs.
    """
    try:
        model = client.models.get(f"{owner}/{name}")
        lv = getattr(model, "latest_version", None)
        return getattr(lv, "id", None) if lv else None
    except Exception:
        return None


def _run_and_get_prediction(model_ref: str, prepared_inputs: dict):
    """Run the model via predictions.create so we can capture the prediction id.

    Returns (output, prediction_id, version_id_or_None).

    When the caller passes a bare slug (no ``:<hash>``), we resolve the current
    latest-version hash and pin to it — the bare-slug predictions path 404s for
    a meaningful subset of older community models, and pinning also makes the
    sidecar's ``version`` field reflect exactly what ran.
    """
    import replicate  # local import
    from replicate import identifier
    from replicate.exceptions import ModelError
    from replicate.helpers import transform_output

    _version, owner, name, version_id = identifier._resolve(model_ref)
    client = replicate.default_client

    if version_id is None and owner and name:
        resolved = _resolve_latest_version(client, owner, name)
        if resolved:
            print(f"[resolve] {owner}/{name} -> :{resolved[:12]}...", file=sys.stderr)
            version_id = resolved

    if version_id is not None:
        prediction = client.predictions.create(
            version=version_id, input=prepared_inputs or {}, wait=True
        )
    elif owner and name:
        prediction = client.models.predictions.create(
            model=(owner, name), input=prepared_inputs or {}, wait=True
        )
    else:
        raise ValueError(f"Invalid model ref: {model_ref}")

    # The blocking create may return before the prediction fully settles.
    if prediction.status in ("starting", "processing"):
        prediction.wait()

    if prediction.status == "failed":
        raise ModelError(prediction)

    output = transform_output(prediction.output, client)
    return output, getattr(prediction, "id", None), version_id


# --- main --------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", help="Model slug (owner/name, optionally :version_id)")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", help="JSON string of model inputs")
    src.add_argument("--input-file", help="Path to a JSON file with model inputs")
    parser.add_argument("--output", default=".", help="Output directory (default: cwd)")
    parser.add_argument("--basename", default=None, help="Base name for output files (default: derived from model slug)")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Disable both sidecar JSON and in-file metadata embedding (default: metadata ON).",
    )
    parser.add_argument(
        "--no-sidecar",
        action="store_true",
        help="Skip writing the .meta.json sidecar but still embed metadata into output files. Useful when you want prompts traveling with each output but no extra JSON files cluttering output dirs.",
    )
    args = parser.parse_args()

    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("ERROR: REPLICATE_API_TOKEN is not set. Get a token at https://replicate.com/account/api-tokens", file=sys.stderr)
        return 1

    try:
        import replicate  # noqa: F401
    except ImportError:
        print("ERROR: `replicate` package not installed. Run: pip install replicate", file=sys.stderr)
        return 1

    if args.input:
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(f"ERROR: --input is not valid JSON: {e}", file=sys.stderr)
            return 1
    else:
        try:
            with open(args.input_file) as f:
                input_data = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: File not found: {args.input_file}", file=sys.stderr)
            return 1
        except OSError as e:
            print(f"ERROR: Could not read {args.input_file}: {e}", file=sys.stderr)
            return 1
        except json.JSONDecodeError as e:
            print(f"ERROR: {args.input_file} is not valid JSON: line {e.lineno} column {e.colno}: {e.msg}", file=sys.stderr)
            return 1

    if not isinstance(input_data, dict):
        print("ERROR: input must be a JSON object", file=sys.stderr)
        return 1

    # Snapshot ORIGINAL user-typed inputs before prepare_inputs() opens file
    # handles — we write these into sidecar / embedded metadata (never the
    # uploaded URIs or open file handles).
    original_inputs_snapshot = json.loads(json.dumps(input_data, default=str))

    prepared_input_data = prepare_inputs(input_data)

    out_dir = pathlib.Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    basename = args.basename or args.model.replace("/", "_").replace(":", "_")

    # Version id from slug if provided (e.g. owner/name:abcd1234)
    slug_version = args.model.split(":", 1)[1] if ":" in args.model else None

    print(f"Running {args.model} ...", file=sys.stderr)
    start = time.time()
    created_at = datetime.now(timezone.utc).isoformat()
    prediction_id: str | None = None
    try:
        output, prediction_id, resolved_version_id = _run_and_get_prediction(args.model, prepared_input_data)
    except Exception as e:
        # Fallback: if our explicit-prediction path breaks for any reason, fall
        # back to the simple replicate.run() path so the user still gets their
        # output. prediction_id stays None in that case.
        print(f"[metadata] predictions.create path failed ({type(e).__name__}: {e}); falling back to replicate.run()", file=sys.stderr)
        try:
            import replicate
            output = replicate.run(args.model, input=prepared_input_data)
            resolved_version_id = slug_version
        except Exception as e2:
            print(f"Replicate call failed: {type(e2).__name__}: {e2}", file=sys.stderr)
            return 1
    completed_at = datetime.now(timezone.utc).isoformat()
    elapsed = time.time() - start
    print(f"Completed in {elapsed:.1f}s", file=sys.stderr)

    saved: list[pathlib.Path] = []

    if isinstance(output, (list, dict)):
        saved.extend(save_output_tree(output, out_dir, basename))
    elif isinstance(output, (str, bytes)):
        saved.append(save_output(output, out_dir, basename))
    elif hasattr(output, "read") and callable(getattr(output, "read", None)):
        saved.append(save_output(output, out_dir, basename))
    elif hasattr(output, "__iter__"):
        # Streaming iterator (e.g., LLM text output)
        chunks = []
        for chunk in output:
            text = str(chunk)
            chunks.append(text)
            sys.stdout.write(text)
            sys.stdout.flush()
        sys.stdout.write("\n")
        path = out_dir / f"{basename}.txt"
        with open(path, "w") as f:
            f.write("".join(chunks))
        saved.append(path)
    else:
        saved.append(save_output(output, out_dir, basename))

    # Metadata: embed + sidecar. Default ON; opt out with --no-metadata.
    if not args.no_metadata:
        resolved_for_meta = resolved_version_id or slug_version
        for p in saved:
            embed_metadata(
                p,
                args.model,
                original_inputs_snapshot,
                version=resolved_for_meta,
                prediction_id=prediction_id,
                runtime_seconds=elapsed,
            )
        if not args.no_sidecar:
            write_sidecar(
                out_dir=out_dir,
                basename=basename,
                model_slug=args.model,
                version=resolved_version_id or slug_version,
                prediction_id=prediction_id,
                created_at=created_at,
                completed_at=completed_at,
                runtime_seconds=elapsed,
                original_inputs=original_inputs_snapshot,
                saved_paths=saved,
            )

    for p in saved:
        print(p)

    return 0


if __name__ == "__main__":
    sys.exit(main())
