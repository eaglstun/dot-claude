---
name: drawthings
version: 1.0.0
public: true
description: >-
  Generate images locally with the Draw Things macOS app's built-in HTTP API
  (AUTOMATIC1111-compatible). Use when the user wants to generate, img2img, or inpaint an
  image through Draw Things, or mentions the Draw Things API.
semantic_id: "LI07MXMzQp_N2StDZ36nq6atCO-z8AAE"
related_ids:
  - "sy09PWv50JsJSaMfYXWX2kbvWOb7AAAL"
  - "IE2i8TWxQxcJiStuYDgz6lncOsGzEAAN"
topic_id: "v2:DFKI"
topic_path: "model-runners/inference-runtimes"
---

# Draw Things

Local image generation through the Draw Things app's built-in HTTP server. The API is
**AUTOMATIC1111-compatible** and runs against whatever model/sampler/settings are loaded
in the app right now — fields you send **override**, fields you omit are **inherited**
from the UI.

**Use the bundled helper [`scripts/drawthings.py`](scripts/drawthings.py)** (stdlib only,
no pip deps): it posts the request, decodes the base64 response to disk, embeds the prompt
in the file metadata, and hints if the server's unreachable. The other two scripts are
[`scripts/caption.py`](scripts/caption.py) (caption a LoRA dataset) and
[`scripts/train_lora.py`](scripts/train_lora.py) (run training). **All three print full
usage with `-h` — run them, don't read their source.** Drop to raw `curl` only for fields
the helper doesn't expose.

## Prerequisites

The Draw Things app must be **open** with a model loaded, and its API server enabled:
**Settings → Advanced → API Server** (Protocol HTTP, Port 7860, IP `localhost`). It's not
a background daemon — if the app is closed, calls fail with a connection-refused hint.

## CLI at a glance

```bash
# See what the app currently has loaded (model, sampler, size) before generating
scripts/drawthings.py config

# Text → image
scripts/drawthings.py txt2img "a fox in a snowy forest, watercolor" \
  -o fox.png --width 768 --height 768 --steps 20 --guidance 5.0

# Image → image (and inpainting with --mask)
scripts/drawthings.py img2img "make it autumn" --init fox.png -o fox_autumn.png --strength 0.6
```

Common flags: `--negative`, `--sampler`, `--seed`, `--model`, `--batch N`,
`--lora FILE[:W]` (repeatable; optional `:weight`, default 1.0), `--url`.
**LoRAs don't inherit from the UI** — with no `--lora` the call uses no LoRA;
passing `--lora` replaces whatever is selected in the app.
Run `scripts/drawthings.py -h` (or `<subcommand> -h`) for everything.

**ControlNet warning (steering with a guide image):** over plain HTTP only **depth** and
**PuLID** work — pose/OpenPose, FLUX Redux, FaceID, inpaint mask, and Union Pro all
**silently no-op** (no error); use the ComfyUI bridge for those. Depth ref goes in
`--init` (img2img), PuLID face in `--control-image` (txt2img), and the control's family
must match the base model or it silently no-ops. Read `references/controlnet.md` before
any control run.

**LoRA training:** a dataset is a folder of images, each with a matching `.txt` caption.
`scripts/caption.py ./dataset` writes the captions via a local Ollama vision model, then
`scripts/train_lora.py` runs training. Full workflow, flags, caption fixing, and the
caption-model choices: `references/cli.md`.

## References - load on demand

- **[references/api.md](references/api.md)** - endpoints, full parameter list, response shape, LAN setup, A1111→DT param renames (`cfg_scale`→`guidance_scale`, `sampler_name`→`sampler`, `denoising_strength`→`strength`). _Read when hand-crafting a request or a field the helper lacks._
- **[references/models.md](references/models.md)** - installed model/LoRA/ControlNet filenames (there's no API to list them). _Read when picking `--model`, `--lora`, or `--control`._
- **[references/controlnet.md](references/controlnet.md)** - what each control needs, HTTP-verified works/fails table, the 10-key control struct, helper examples. _Read before any ControlNet/adapter run._
- **[references/cli.md](references/cli.md)** - headless `draw-things-cli`, captioning (models, correction flags), the full `train_lora.py` workflow. _Read for LoRA training or app-closed generation._
- **[references/grpc.md](references/grpc.md)** - the gRPC interface: mask/hints, the headless full-control path. _Read when HTTP can't express the job._
- **[references/comfyui-bridge.md](references/comfyui-bridge.md)** - ComfyUI bridge setup/run/connection, the full-control GUI path. _Read when a control silently no-ops over HTTP._
- **[references/ecosystem.md](references/ecosystem.md)** - the drawthingsai GitHub repos (CLI, gRPC, scripts, docs). _Read when hunting upstream source or docs._

## Saving artifacts

1. Use a descriptive filename in the cwd (`fox_snow.png`, not `output.png`) and pass
   `-o <path>` so bytes land on disk, never in context.
2. The helper embeds the prompt + model into the file metadata via `exiftool`
   (`brew install exiftool` if missing — it skips silently otherwise; verify with
   `exiftool -Comment -Description <file>`). Matches the `pollinations`/`together`/`replicate`
   provenance rule.
3. Report the saved path back — the harness displays images inline.

## Notes & gotchas

- The API inherits unset fields from the **current UI state**, including any **ControlNet /
  LoRA loaded in the app**. These ride along on every call; if output looks unexpectedly
  face-locked or stylized, run `config` to see the active model, size, sampler, `controls`,
  and `loras`.
- Default URL is `http://127.0.0.1:7860`. For another LAN device, set the app's IP to
  `0.0.0.0` and pass `--url http://<your-mac-lan-ip>:7860` (your machine on the LAN).
- No auth on the API. Keep it `localhost` unless you intend LAN access.
