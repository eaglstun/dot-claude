# ComfyUI ↔ Draw Things gRPC bridge (setup & run)

The [draw-things-comfyui](https://github.com/drawthingsai/draw-things-comfyui) extension
drives Draw Things from ComfyUI over **gRPC** — the path that exposes the **mask** and
**hints** channels the HTTP API and CLI lack (see [`grpc.md`](grpc.md)). Set up and
**verified connected** on this Mac on 2026-06-01.

## What's installed (this machine)

| Piece                                                                    | Location                                                                                       |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| gRPC server binary                                                       | `/usr/local/bin/gRPCServerCLI-macOS` (Homebrew? standalone — already present)                  |
| ComfyUI (**upstream** `comfyanonymous`, not the stale drawthingsai fork) | `~/Documents/dev/ComfyUI`                                                                      |
| ComfyUI venv (Python 3.12, torch 2.12 + MPS)                             | `~/Documents/dev/ComfyUI/venv`                                                                 |
| Bridge node                                                              | `~/Documents/dev/ComfyUI/custom_nodes/draw-things-comfyui` (web assets prebuilt in `web/dist`) |

> ⚠️ Use **upstream** ComfyUI. The org's `drawthingsai/ComfyUI` fork is ~2700 commits
> behind and irrelevant — the bridge is a custom node that runs in current ComfyUI.

## Start the three pieces

```bash
# 1) gRPC server — point at the Draw Things models dir (port 7859). --no-tls for local.
/usr/local/bin/gRPCServerCLI-macOS \
  "$HOME/Library/Containers/com.liuliu.draw-things/Data/Documents/Models" \
  --no-tls --no-response-compression --model-browser
#   (TLS is recommended for non-local use; the bridge has a use_tls toggle.)

# 2) ComfyUI
cd ~/Documents/dev/ComfyUI && ./venv/bin/python main.py --port 8188
#   → http://127.0.0.1:8188

# 3) Bridge node loads automatically with ComfyUI (custom_nodes/). No build needed.
```

The gRPC server does **not** need the Draw Things app open (it loads models itself); it
can run alongside the app's HTTP API (:7860) without conflict.

## Use it

Open <http://127.0.0.1:8188>, load an example workflow from
`custom_nodes/draw-things-comfyui/example_workflows/` (**Text to Image**, **Inpainting**,
**LoRAs, Upscaler and Refiner**), and on the **DrawThingsSampler** node set the server to
`127.0.0.1` / port `7859` (TLS off, matching the `--no-tls` server).

Nodes the bridge provides: `DrawThingsSampler`, `DrawThingsControlNet`, `DrawThingsLoRA`,
`DrawThingsPositive` / `DrawThingsNegative` / `DrawThingsPrompt`, `DrawThingsRefiner`,
`DrawThingsUpscaler`, **`DrawThingsHints`** (the control-hints channel), plus
`SDPoseDrawKeypoints` and `DrawBBoxes` helpers.

## Debug routes (bridge → server)

The node registers HTTP routes under ComfyUI:

```bash
# List models/files on a local gRPC server (the connection test used to verify setup):
curl -s -X POST http://127.0.0.1:8188/dt_grpc/files_info \
  --data server=127.0.0.1 --data port=7859 --data use_tls=false
#   → {"models":[{file, name, version, autoencoder, text_encoder, recommended settings…}]}
```

Other routes: `/dt_grpc/combined_models` (curated catalog from a GitHub Pages JSON),
`/dt_grpc/bridge_models` (the **DT+ cloud** at `compute.drawthings.ai`, not local),
`/dt_grpc/sync_settings`, `/dt_grpc/interrupt`.

## Verified ✅ — end-to-end generation works

Full stack installs and runs; the bridge node imports cleanly; `files_info` returns the
live model catalog from the local gRPC server; **and a text-to-image generation completed
through the bridge** (ComfyUI → gRPC → Z-Image Turbo → a clean fox in the snow, saved as
`../output/bridge_text2img.png`). `status: success`, no node errors.

## Control battery through the bridge (2026-06-01)

Ran the controls that no-op'd over HTTP/CLI through the bridge. **Three of them now work**
— the bridge reaches plumbing the other interfaces couldn't. Results (all A/B'd by
swapping the reference and measuring pixel diff):

- **Inpaint — ✅ WORKS.** `DrawThingsSampler` with `image` (fox) + `mask` (right third,
  via `LoadImageMask`) + `preserve_original=True` on `sd_v1.5_inpainting` → the fox was
  **preserved** and only the masked region changed (`../output/bridge_inpaint.png`). HTTP
  and CLI erased the whole frame; the gRPC **mask channel delivers true regional inpaint**.
- **Redux — ✅ WORKS.** `DrawThingsControlNet(control_name=flux_1_redux,
control_input_type="Shuffle", image=ref)` → `control_net`, on FLUX, prompt "a photo".
  Fox-ref → a fox; redhead-ref → the redhead (diff **56/255**, both reference-faithful).
  HTTP/CLI gave the same seed-only image regardless of reference; the bridge conditions on
  it. Files `../output/bridge_redux2_fox.png` / `bridge_redux2_face.png`.
- **FaceID (Kolors) — ✅ WORKS.** `DrawThingsControlNet(control_name=ip_adapter_faceid_plus_kwai_kolors,
control_input_type="Custom", image=face)` → `control_net`, on Kolors. Redhead-ref → the
  redhead; bearded-man-ref → the bearded man (diff **99/255**, faithful identity transfer).
  HTTP/CLI produced unrelated faces. Files `../output/bridge_faceid_*.png`.
- **Moodboard hint alone — ❌ negligible.** `DrawThingsHints(type="Shuffle (Moodboard)")`
  without a paired control_net: server logs `ControlHintType: shuffle` but output barely
  changes (diff 0.03). Reference adapters need the **control_net** wired (as Redux above),
  not just the hint.
- **Pose — ✅ WORKS** (once two conditions are met). Arms-down skeleton → robot with arms
  at its sides; arms-up skeleton → robot with arms raised (diff **23/255**, poses match).
  Files `../output/bridge_sd2pose_down.png` / `bridge_sd2pose_up.png`. Two requirements,
  both of which silently no-op the control if wrong:
  1. **Pre-rendered skeleton, not a raw photo.** DT does **not** extract a pose skeleton
     from a photo (only **Depth** is auto-extracted). Feed an actual OpenPose skeleton via
     `control_input_type="Custom"` (passthrough). I hand-rendered one with PIL (COCO-18
     limbs + standard OpenPose colors); a ComfyUI OpenPose preprocessor would also work.
  2. **Family match.** `controlnet_openpose_2.x` is an **SD 2.x** control — it must pair
     with an SD 2.x model (`sd_v2.1`), **not** `sd_v1.5`. A family mismatch produces a
     `custom` hint server-side but **silently no-ops** (pixel-identical output) — this is
     what made every earlier pose attempt fail (wrong family **and** raw photo).

**Takeaway:** the bridge unlocks **all four** controls that no-op'd on HTTP/CLI — inpaint
(mask channel), Redux, FaceID, and pose. The pattern that works: `DrawThingsControlNet`
with `control_name` + the input on the node's `image` input + the right
`control_input_type`, fed to `sampler.control_net`. Two rules learned the hard way, each
of which causes a **silent no-op** (not an error):

1. **Family must match.** SD-2.x control + SD-2.x model, FLUX + FLUX, Kolors + Kolors. A
   mismatch creates the hint server-side but does nothing.
2. **Structural controls need a pre-extracted map.** DT auto-extracts only **Depth** from
   a raw image; pose/canny/scribble/etc. need a ready-made hint map fed via `Custom`.

Reference adapters (Redux/FaceID) take the raw reference directly (no preprocessing).
Diagnosing silent no-ops: the gRPC server log (`Created ControlHintType: …`) confirms the
hint was sent, and a **byte/pixel A/B** (swap the input, measure the diff) confirms whether
it actually affected the output — eyeballing one image is how the earlier mirages happened.

## Headless generation via the API (reproducible recipe)

The example workflows are UI-format; to queue headlessly, POST an **API-format** prompt to
`/prompt`. The only non-obvious input is `model`, which the node expects as
`{"value": <full model object from /dt_grpc/files_info>}` (it reads `.file` and
`.version` off it). `positive`/`negative` are plain optional strings — no prompt node
needed. Minimal graph that worked:

```python
# 1) model object from the catalog
cat = POST /dt_grpc/files_info  (server, port, use_tls=false)   # {"models":[{file,version,...}]}
model_obj = next(m for m in cat["models"] if m["file"] == "z_image_turbo_1.0_q8p.ckpt")

# 2) DrawThingsSampler inputs = node defaults from /object_info, then override:
#    server=127.0.0.1, port=7859, use_tls=False, model={"value": model_obj},
#    seed, width, height, steps, cfg, positive, negative
prompt = {
  "1": {"class_type":"DrawThingsSampler", "inputs": {...}},
  "2": {"class_type":"SaveImage", "inputs": {"images":["1",0], "filename_prefix":"dt_bridge"}},
}
POST /prompt {"prompt": prompt}            # → {"prompt_id": ...}; check node_errors
# poll GET /history/<prompt_id> until status.completed; outputs[*].images[*].filename
```

Output lands in `ComfyUI/output/`. This recipe is the harness for testing the
mask/hints-dependent controls (inpaint, pose, redux, FaceID) headlessly via gRPC — the
ones that no-op'd over HTTP/CLI.

## Notes

- Bridge Python deps live in the ComfyUI venv: `grpcio`, `flatbuffers`, `protobuf`,
  `fpzip` (these encode the FlatBuffer `configuration` and handle the gRPC transport —
  the hard part we'd otherwise hand-roll).
- Known upstream issue: bridge #4 "does not list custom models" (see [`ecosystem.md`](ecosystem.md)).
