# ControlNet & adapters in Draw Things

ControlNet lets you **steer a generation with a guide image** instead of words alone —
"draw a robot, but in _this_ pose" or "this scene, but with _this_ person's face."
Draw Things does this through its own native **`controls`** array, **not** the
AUTOMATIC1111 `alwayson_scripts.controlnet` mechanism (that does nothing here).

> **This page covers the HTTP API.** Most controls (inpaint, pose, Redux, FaceID) only
> truly work over the **gRPC / ComfyUI bridge** — see [`comfyui-bridge.md`](comfyui-bridge.md),
> which has them all verified working (incl. pose, with a pre-rendered skeleton + a
> family-matched model). Over plain HTTP, **only depth still works** — PuLID regressed
> (see below).

## What actually works over the HTTP API (verified)

This was tested control-by-control on the live API. The honest headline: **only depth
still produces its effect over HTTP** (PuLID did until mid-2026 and no longer does),
because the others depend on a preprocessing or reference step the HTTP shim doesn't run
(the app GUI does it for you).

> **PuLID regression — re-tested 2026-07-26.** Same seed, same prompt, `weight 1.0`,
> `controlImportance: control`, FLUX.1 [dev] q8p base, face on `control.image` per the
> documented recipe — then the reference was swapped for a **completely different
> person**. Output RMSE: **0.000536 normalized (0.05%)**, visually the identical image.
> The adapter is effectively inert. Not a family mismatch (FLUX control + FLUX model) and
> not a payload error (HTTP 200, no warning). Cause unconfirmed — suspect an app-version
> change in how the `arcface` embedding is fetched over the HTTP shim.
> **For local identity work, use the ComfyUI/gRPC bridge or the app UI.**

| Control                                              | Works over HTTP?      | How                                                                    |
| ---------------------------------------------------- | --------------------- | ---------------------------------------------------------------------- |
| **Depth** (`controlnet_depth_1.x_v1.1_f16.ckpt`, SD) | ✅ yes                | img2img, guide in `init_images`, `strength 1.0`                        |
| **PuLID** identity (`pulid_0.9.1_…_f16.ckpt`, FLUX)  | ⚠️ **no (regressed)** | was ✅ on 2026-06-01; **re-tested 2026-07-26: inert** — see below      |
| OpenPose (SD), Kolors pose                           | ❌ no                 | needs a pre-extracted pose skeleton; DT doesn't auto-extract over HTTP |
| Union Pro 2.0 (FLUX)                                 | ❌ no                 | needs a pre-extracted control map                                      |
| FLUX.1 Redux                                         | ❌ no                 | reference image ignored in every payload tried                         |
| Alimama Inpaint (FLUX)                               | ❌ no                 | mask channel not accepted / unknown                                    |
| Kolors IP-Adapter FaceID                             | ❌ no                 | face embedding never engaged                                           |

The rule of thumb that came out of testing: **DT auto-preprocesses _depth_ over HTTP,
but not pose / canny / union** — those expect you to feed an already-extracted control
map (an actual depth/edge/skeleton image), which the GUI generates and the API doesn't.
**No identity adapter currently works over HTTP** — PuLID was the last one and regressed
(2026-07-26). For identity, and for everything in the ❌ rows, **use the app UI or the
gRPC/ComfyUI bridge**.

### Why the ❌ controls can't work over HTTP (re-tested 2026-06-01)

After making pose/Redux/FaceID **all work over the gRPC bridge** (see
[`comfyui-bridge.md`](comfyui-bridge.md)), the obvious question was whether they'd work
over HTTP too, given the right wiring (family match + reference on `control.image` + the
right `inputOverride`). **They don't** — re-tested each over HTTP with every fix we learned
(family-matched models, pre-rendered skeleton in both `control.image` and `init_images`,
`inputOverride` = `shuffle`/`custom`/`pose`/`""`). Every one returned **0.0 pixel diff**
when the reference was swapped — confirmed no-ops.

The reason is structural: **two input channels exist only in gRPC**, not the HTTP API:

- The **`hints`** channel (`HintProto`) — carries pre-extracted control maps and reference
  tensors (pose skeletons, Redux/FaceID references, shuffle/moodboard). Pose, Redux, and
  FaceID all need it.
- The first-class **`mask`** field — HTTP rejects `mask` outright
  (`Unrecognized keys: ["mask"]`), so regional inpaint is impossible over HTTP.

What HTTP _can_ do: plain txt2img/img2img, **depth** (the engine auto-extracts it from the
init image), and **PuLID** (its reference fits in `control.image`). Curiosity:
**PuLID works over HTTP but FaceID doesn't**, though both are identity adapters —
architecture-specific (PuLID routes through `control.image`; FaceID wants the hint
channel). Observed, not fully explained. Net: **the bridge/gRPC adds real capability here,
not just convenience.**

## The two working mechanisms

| Kind                            | Control | How the image is delivered                                 | Endpoint                     |
| ------------------------------- | ------- | ---------------------------------------------------------- | ---------------------------- |
| **Structural** (match a layout) | Depth   | as the **`init_images`** image (DT extracts the depth map) | **img2img**, `strength: 1.0` |
| **Identity** (match a face)     | PuLID   | as an **`image` field inside the control entry**           | **txt2img**                  |

A face reference for PuLID does **not** go in `init_images` — if you put it there it
fights the generation and the identity never transfers (verified: it produced a
completely different person). It goes on the control entry. In both cases:
_guide/reference image = structure or identity, prompt = everything else._

## The strict rules (or you get HTTP 422)

1. **Every control entry is a complete struct** — all keys present, even at defaults, or
   you get `keyNotFound: 'guidanceStart'` (or whichever key you dropped):

   ```json
   {
     "file": "controlnet_depth_1.x_v1.1_f16.ckpt",
     "weight": 1.0,
     "guidanceStart": 0.0,
     "guidanceEnd": 1.0,
     "noPrompt": false,
     "inputOverride": "",
     "controlImportance": "balanced",
     "targetBlocks": [],
     "downSamplingRate": 0.0,
     "globalAveragePooling": false
   }
   ```

   Identity controls add an extra `"image": "<base64>"` key to this struct.

2. **Match families** — a FLUX control with a FLUX model, an SD control with an SD model,
   a Kolors control with a Kolors model. A mismatch does **not** error — it silently
   no-ops, so "control did nothing" can always be a family mismatch.

3. **Structural controls need img2img.** `txt2img` rejects `init_images`
   (`"init_images is not supported for text-to-image"`). Use `strength: 1.0` so the init
   acts purely as the control source and doesn't tint the output. Identity controls use
   `txt2img` and carry their image on the control entry instead.

## Field reference

| Key                                                        | Meaning                                                                                                                            |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `file`                                                     | the control model `.ckpt` (see [`models.md`](models.md))                                                                           |
| `image`                                                    | **identity controls only** — base64 reference image on the control entry                                                           |
| `weight`                                                   | influence strength; `1.0` = full, lower = looser adherence                                                                         |
| `guidanceStart` / `guidanceEnd`                            | fraction of the denoise (0–1) the control is active. `0→1` = whole run; `0→0.5` shapes early structure then lets the prompt finish |
| `controlImportance`                                        | tug-of-war vs. the prompt: `balanced` (default), `prompt`, `control`. Unrecognized values fall back to default                     |
| `noPrompt`                                                 | run the control with the prompt ignored                                                                                            |
| `inputOverride`                                            | override the control's input source / preprocessor mode; `""` = default                                                            |
| `targetBlocks`, `downSamplingRate`, `globalAveragePooling` | advanced; leave at `[]` / `0` / `false`                                                                                            |

## Easiest path — the helper script

`scripts/drawthings.py` builds the full struct for you (so you can't trip rule #1).

```bash
# STRUCTURAL — depth: a robot that inherits the layout/pose of the guide photo.
# Guide image is --init, so use img2img with --strength 1.0.
scripts/drawthings.py img2img "a chrome robot statue, studio photo" \
  --init depth_ref.png -o robot.png \
  --model sd_v1.5_f16.ckpt --strength 1.0 \
  --control controlnet_depth_1.x_v1.1_f16.ckpt

# IDENTITY — PuLID: put a known face into a new scene.
# Face reference is --control-image (NOT --init), on txt2img.
scripts/drawthings.py txt2img "a portrait as a renaissance oil painting, ornate background" \
  -o portrait.png --model flux_1_dev_q8p.ckpt --guidance 3.5 \
  --control pulid_0.9.1_eva02_clip_l14_336_f16.ckpt \
  --control-image face_ref.png
```

`--control` is repeatable to **stack controls**; `FILE:WEIGHT` sets a per-control weight;
`--control-importance` is `balanced` (default) / `prompt` / `control`.

**Verified examples:**

- _Depth:_ a seated-fox photo through `controlnet_depth_1.x` + prompt "a chrome robot
  statue" → a robot in the fox's exact seated pose and silhouette.
- _PuLID:_ a red-haired freckled portrait as `--control-image` + prompt "renaissance oil
  painting" → the same face and freckles, repainted in oils. (Hair color/style follows
  the prompt — PuLID carries facial identity, not hairstyle.)

## Not working over HTTP (as tested) — use the app UI

Documented so nobody re-runs the safari. All of these would not produce their effect
through the HTTP API with any payload tried.

- **OpenPose (SD) & Kolors pose** — fed a clear full-body human standing reference via
  `init_images`. Result was a **generic robot, not the reference pose** (~3 s, no sign of
  skeleton extraction). Unlike depth, DT does **not** auto-run the pose preprocessor over
  HTTP — pose controls want an already-extracted **OpenPose skeleton image** as input.
- **Union Pro 2.0 (FLUX)** — raw photo via `init_images` _and_ a per-control `image`,
  with `inputOverride` = `depth`/`canny`/`pose`/`scribble`/`custom`. Outputs varied but
  never matched the reference structure. Union ControlNets want a **pre-extracted control
  map**, not a raw photo.
- **FLUX.1 Redux** — reference via control `image` (txt2img) and `init_images` (img2img,
  strength 1.0 and 0.7). At strength 1 the reference was ignored; at 0.7 it was just plain
  img2img preservation. No variation behavior.
- **Alimama Inpaint Beta (FLUX)** — top-level `mask` is rejected
  (`Unrecognized keys: ["mask"]`); mask as the init's **alpha channel** or as a **second
  `init_images` entry** both produced garbled output. The helper's `--mask` flag was
  removed because it can only 422.
- **Kolors IP-Adapter FaceID** — face via control `image` (txt2img, incl. `weight 2.0` /
  `controlImportance: control`) and via `init_images` (img2img). Identity never
  transferred (unrelated faces, ~5 s — the embedding never engaged), even with the Kolors
  base model installed.

> Why the GUI succeeds where HTTP doesn't: the app runs the **preprocessors** (depth
> extraction, pose detection, edge maps) and manages **reference/mask slots** before the
> pipeline runs. The HTTP API is a thinner shim that passes only depth through that
> machinery. The native gRPC interface _may_ expose more of it — untested.

## Gotchas

- **422 `keyNotFound`** → control struct missing a key. Send all ten. (The helper does
  this for you.)
- **`init_images is not supported for text-to-image`** → guide image on `txt2img`. Depth
  goes through `img2img --init`.
- **Identity control had no effect / wrong face** → for PuLID, pass the face as
  `--control-image` on `txt2img`, not `--init` (as `--init` it competes with the gen).
- **Control silently did nothing** → family mismatch (DT no-ops instead of erroring), or
  it's a pose/canny/union control that needs a pre-extracted map, or a reference adapter
  that doesn't engage over HTTP (see the list above).
- **Output tinted like the guide photo** → raise `--strength` toward `1.0`.
