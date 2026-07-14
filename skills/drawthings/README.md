# drawthings

Claude Code skill for local image generation through the **Draw Things** macOS app's
built-in HTTP API (`http://127.0.0.1:7860`) — text-to-image, image-to-image, and
inpainting. The API is AUTOMATIC1111-compatible and runs against the model/settings
currently loaded in the app.

## Setup

Open the Draw Things app, load a model, and enable the server:
**Settings → Advanced → API Server** (Protocol HTTP, Port 7860, IP `localhost`).
The server only runs while the app is open — there's no daemon. For LAN access set the
IP to `0.0.0.0` and reach it at the Mac's address (`http://<your-mac-lan-ip>:7860`).

`exiftool` (`brew install exiftool`) is optional but recommended — the helper uses it to
embed the prompt/model into each saved image.

## Usage

`SKILL.md` is the entry point. The bundled `scripts/drawthings.py` (stdlib only) wraps
the API:

```bash
scripts/drawthings.py config                              # dump current app config
scripts/drawthings.py txt2img "a fox in snow" -o fox.png  # text → image
scripts/drawthings.py img2img "make it autumn" --init fox.png -o fox2.png --strength 0.6
```

Endpoints, full parameter list, and A1111 param-name gotchas live in
[`references/api.md`](references/api.md). A running inventory of installed models,
LoRAs, and ControlNets (with the exact filenames to pass as `model`) is in
[`references/models.md`](references/models.md) — Draw Things has no model-listing API,
so that list is built from the on-disk model folder. How to steer generations with a
guide image (pose, depth, identity, inpaint) is in
[`references/controlnet.md`](references/controlnet.md).

Gotcha: the API **inherits unset fields from the UI** (run `config` to see what's
loaded), and renames a few A1111 params — `cfg_scale` → `guidance_scale`,
`sampler_name` → `sampler`, `denoising_strength` → `strength`.
