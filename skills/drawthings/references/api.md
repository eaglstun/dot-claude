# Draw Things HTTP API reference

The Draw Things macOS/iOS app ships a built-in HTTP server that is
**AUTOMATIC1111-compatible**. It runs against whatever model, sampler, LoRAs, and
settings are currently loaded in the app's UI — the API **overrides** the fields you
send and **inherits** everything you omit. There is no separate "reset to defaults".

## Enabling the server

In the app: **Settings → Advanced → API Server**.

| Setting  | Value                                                     |
| -------- | --------------------------------------------------------- |
| Protocol | HTTP                                                      |
| Port     | 7860 (default)                                            |
| IP       | `localhost` for same-machine use; `0.0.0.0` to expose LAN |

- Base URL (local): `http://127.0.0.1:7860`
- Base URL (LAN, from the Pi or another device): `http://<your-mac-lan-ip>:7860`
  (your machine on the LAN). Requires IP set to `0.0.0.0` in the app.
- No auth/token. Keep it `localhost` unless you specifically want LAN access.

The app must be **open and in the foreground** with a model loaded; the server is not
a background daemon. If the model picker is mid-download or no model is selected,
generation calls will fail.

## Endpoints

### `GET /` — current configuration

Returns the app's current setup (selected model, sampler, size, steps, etc.) as JSON.
Use it to discover valid values before generating.

```bash
curl -s http://127.0.0.1:7860/ | python3 -m json.tool
```

### `POST /sdapi/v1/txt2img`

Generate from a text prompt. JSON body — common fields:

| Field             | Type   | Notes                                               |
| ----------------- | ------ | --------------------------------------------------- |
| `prompt`          | string | required                                            |
| `negative_prompt` | string |                                                     |
| `width`           | int    | inherits UI value if omitted                        |
| `height`          | int    |                                                     |
| `steps`           | int    | sampling steps                                      |
| `guidance_scale`  | float  | CFG scale — Draw Things' name for `cfg_scale`       |
| `sampler`         | string | e.g. `"DPM++ 2M Karras"`, `"Euler a"`               |
| `seed`            | int    | `-1` / omit for random                              |
| `model`           | string | model filename; omit to use the app's current model |
| `batch_count`     | int    | number of images                                    |

Response:

```json
{ "images": ["<base64 PNG>", "..."], "parameters": { ... }, "info": "..." }
```

`images` is an array of base64-encoded PNGs (raw base64, no `data:` prefix). Decode and
write to disk — never echo base64 into the conversation.

```bash
curl -s http://127.0.0.1:7860/sdapi/v1/txt2img \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"a fox in a snowy forest, watercolor","width":768,"height":768,"steps":20,"guidance_scale":5.0}' \
  | python3 -c 'import sys,json,base64;open("fox.png","wb").write(base64.b64decode(json.load(sys.stdin)["images"][0]))'
```

### `POST /sdapi/v1/img2img`

Same fields as txt2img, plus:

| Field         | Type            | Notes                                                 |
| ------------- | --------------- | ----------------------------------------------------- |
| `init_images` | array of base64 | source image(s); the helper script fills this for you |
| `strength`    | float 0..1      | denoising strength — higher = further from the source |
| `mask`        | base64          | optional mask for inpainting                          |

Response shape is identical to txt2img.

## Param-name gotchas vs. AUTOMATIC1111

Draw Things diverges from stock A1111 names on a few fields — when porting an A1111
payload, translate these:

| A1111                            | Draw Things      |
| -------------------------------- | ---------------- |
| `cfg_scale`                      | `guidance_scale` |
| `sampler_name` / `sampler_index` | `sampler`        |
| `n_iter` / `batch_size`          | `batch_count`    |
| `denoising_strength` (img2img)   | `strength`       |

When unsure of a value, `GET /` to see exactly what the app expects.

## Inherited state — the big gotcha

The API overrides the fields you send and **inherits everything else from the current
UI state**, including things you can't pass in a basic txt2img payload:

- **Loaded ControlNets / adapters / LoRAs ride along.** If the app has e.g. a **PuLID**
  identity control or a LoRA selected, every API generation inherits it — even a plain
  text prompt. If outputs come back unexpectedly face-locked, stylized, or otherwise
  "stuck", an inherited control/LoRA in the UI is the usual cause. Clear it in the app,
  or `GET /` and check the `controls` / `loras` arrays.
- **Model, size, sampler, steps** all default to whatever's selected in the UI. Run
  `GET /` first if you need to know what you're actually getting.

## No model-listing endpoints

Unlike stock AUTOMATIC1111, Draw Things does **not** implement the listing endpoints —
`/sdapi/v1/sd-models`, `/samplers`, `/loras`, `/upscalers` all return empty. To
enumerate installed models, read the on-disk model folder; see
[`models.md`](models.md). `/sdapi/v1/options` works but just echoes the current config
(same data as `GET /`).

## Provenance caveat

When you omit `model`, the response/metadata can't name the model that was actually
used (the helper stamps `Software=drawthings` rather than `drawthings/<model>`). Pass
`--model` explicitly if you want the model name embedded in the saved file.

## gRPC server (headless alternative)

For headless / scripted generation without the GUI, Draw Things also offers a separate
**gRPC Server** (`gRPCServerCLI`, also runnable as a community Docker image). That is a
different protocol and is out of scope for this skill — this skill targets the in-app
HTTP API. Reach for the gRPC server only if you need to run on a machine with no GUI
session.
