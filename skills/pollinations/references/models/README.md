# Model reference

Per-model pages: what a model is, what it takes, what it costs, what it can't do, and copy-pasteable CLI + API invocations. Consult before picking a model — especially when balance matters or the user requests something model-specific.

The live source of truth for pricing and modalities is the API:

```bash
polli models --json                  # everything
polli models --type video --json     # just video
curl https://gen.pollinations.ai/image/models  # image + video, no auth
```

Pages here add context the API doesn't carry: provider heritage, prompt-engineering tips, known quirks.

## Video

| Model       | Input        | Free                                     | Duration            | Resolution  | Price (pollen/sec)              | Page                           |
| ----------- | ------------ | ---------------------------------------- | ------------------- | ----------- | ------------------------------- | ------------------------------ |
| `ltx-2`     | text         | ✅                                       | up to 10s           | upscaled    | **0.005**                       | [`ltx-2.md`](ltx-2.md)         |
| `wan-fast`  | text + image | paid                                     | ~5s                 | 480p        | 0.015 (+0.015 audio)            | [`wan-fast.md`](wan-fast.md)   |
| `p-video`   | text + image | paid                                     | up to ~10s          | up to 1080p | 0.036                           | [`p-video.md`](p-video.md)     |
| `wan`       | text + image | paid                                     | 2–15s               | up to 1080p | 0.075 + 0.075 audio (always on) | [`wan.md`](wan.md)             |
| `nova-reel` | text + image | no `paid_only` flag, but 16× ltx-2 price | **6–60s** (longest) | 720p        | 0.08                            | [`nova-reel.md`](nova-reel.md) |

Other video models (not yet documented here, see `references/video.md` for a summary): `veo`, `seedance`, `seedance-pro`, `grok-video-pro`.

## Image

| Model       | Input        | Free                 | Seed / Negative | Price (pollen/image-token)                | Page                           |
| ----------- | ------------ | -------------------- | --------------- | ----------------------------------------- | ------------------------------ |
| `flux`      | text         | ✅                   | seed + negative | **0.001**                                 | [`flux.md`](flux.md)           |
| `zimage`    | text         | ✅                   | seed + negative | 0.002 (default model, 2× upscaled output) | [`zimage.md`](zimage.md)       |
| `klein`     | text + image | ✅ (not `paid_only`) | seed only       | 0.01 (fast editing, FLUX.2 4B)            | [`klein.md`](klein.md)         |
| `kontext`   | text + image | ✅ (not `paid_only`) | neither         | 0.04 (best in-context editing)            | [`kontext.md`](kontext.md)     |
| `p-image`   | text         | paid                 | neither         | 0.0075                                    | [`p-image.md`](p-image.md)     |
| `seedream5` | text + image | paid                 | seed only       | 0.0525 (web search + reasoning)           | [`seedream5.md`](seedream5.md) |

Other image models (see `references/image.md` for summaries): `gptimage`, `gptimage-large`, `wan-image`, `wan-image-pro`, `qwen-image`, `nanobanana`, `nanobanana-2`, `nanobanana-pro`, `grok-imagine`, `grok-imagine-pro`, `p-image-edit`, `nova-canvas`.

## Audio, text

Not split into per-model pages yet. See `references/audio.md`, `references/text.md` for the full lists with short descriptions, and `references/reference.md` for complete tables.

## When to write a new model page here

Write one when you hit a model-specific detail worth remembering: a prompt pattern that works well, a param that's silently ignored, a resolution ceiling the API doesn't advertise, a cost surprise. Keep pages short — link to `reference.md` for anything shared across models.
