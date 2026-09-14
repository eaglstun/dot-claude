# Video models on Replicate

Model schemas drift; verify the model page on replicate.com before relying on exact field names or ranges. The selection table and defaults below are accurate as of 2026-Q2.

## Selection guide

| Use case                       | Model                                        | Why                                                                                                   |
| ------------------------------ | -------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Default text-to-video**      | `bytedance/seedance-2.0`                     | Fast, good quality, native audio on by default, up to 15s, multimodal refs                            |
| Widest reference-input menu    | `bytedance/seedance-2.0`                     | Up to 9 `reference_images` + 3 `reference_videos` + 3 `reference_audios` in one run                   |
| Highest visual quality         | `runwayml/gen-4.5`                           | Top of Artificial Analysis benchmark; best physics/coherence                                          |
| Dialogue / lip sync (T2V)      | `google/veo-3.1` or `kwaivgi/kling-v3-video` | Native audio with speech                                                                              |
| Image-to-video                 | `minimax/hailuo-2.3`                         | Solid T2V + I2V, realistic motion                                                                     |
| Image-to-video (open weights)  | `wan-video/wan-2.7-i2v`                      | Four modes (i2v, first-last, clip continuation, audio-sync), up to 15s 1080p                          |
| Open-source weights            | `wan-video/wan-2.7-t2v`                      | 27B MoE, fast variants for iteration                                                                  |
| Fastest open-source            | `lightricks/ltx-video`                       | Often faster than realtime, ~$0.08/run, 24fps; needs long prompts                                     |
| Named camera moves             | `minimax/video-01-director`                  | Bracketed directives like `[Push in]`, `[Pan left]` for repeatable camera control                     |
| Long clips with audio          | `vidu/q3-pro`                                | Up to 16s at 1080p, three modes, synced audio                                                         |
| Multi-mode (gen + edit + ref)  | `kwaivgi/kling-v3-omni-video`                | T2V, I2V, reference-based (up to 7 chars), video edit, multi-shot — one endpoint                      |
| Cheapest (draft mode)          | `prunaai/p-video`                            | $0.005/s at 720p draft (~$0.025 for 5s); also handles i2v, start-end, audio-driven                    |
| Cheapest (cinematic)           | `pixverse/pixverse-v6`                       | $0.05/s at 360p; supersedes v5.6 — better camera, text rendering, multi-shot switch                   |
| Named video effects (v5-only)  | `pixverse/pixverse-v5`                       | 15-value `effect` enum (YMCA, Ghibli Live!, Kungfu Club, Vogue Walk, Mega Dive, …)                    |
| Fastest (~30s wall time)       | `xai/grok-imagine-video`                     | Short clips with synced audio, many aspect ratios                                                     |
| Face restoration in video      | `zsxkib/stable-video-face-restoration`       | SVD-based face restore with temporal stability; also colorizes / inpaints faces                       |
| Change aspect ratio (outpaint) | `luma/reframe-video`                         | Generative reframe — invents new content on the sides, not a crop/blur; picks a target `aspect_ratio` |

**Default pick when the user hasn't specified:** `bytedance/seedance-2.0` with `duration: 5`, `aspect_ratio: "16:9"`. Call out the cost before using premium models (runway, veo).

**`pixverse/pixverse-v5.6` note:** v5.6 is superseded by `pixverse/pixverse-v6` for new work — v6 adds cinematic camera control, in-frame text rendering, multi-shot via `generate_multi_clip_switch`, and first-person POV. Mention v5.6 only if the user is reproducing older output.

**`pixverse/pixverse-v5` note:** v6 also supersedes v5 for normal work. The **only** reason to reach for v5 is its 15-value `effect` enum — named one-shot presets like `"Let's YMCA!"`, `"Ghibli Live!"`, `"Kungfu Club"`, `"Vogue Walk"`, `"Mega Dive"`, `"Evil Trigger"`, `"Retro Anime Pop"` — which v6 removed entirely. v5 is **not** a cheap-draft alternative: its cheapest tier is comparable to v6 540p and its billing model (Replicate units) is less transparent than v6's $/second. v5 also has `duration: 5|8` only (v6 adds `10|15`), gates `quality: "1080p"` to 8s (v6 removes that restriction), and lacks `generate_audio_switch` / `generate_multi_clip_switch` — output is silent, single-shot. Reach for v5 when you specifically need one of the effect presets; otherwise default to v6.

## Common inputs

Most text-to-video models accept some subset of:

- `prompt` — text description of the scene (required)
- `duration` — seconds (usually 5, 6, 8, 10, or 15 depending on model)
- `aspect_ratio` — `"16:9"`, `"9:16"`, `"1:1"`
- `resolution` — `"720p"` or `"1080p"`
- `seed` — integer for reproducibility
- `negative_prompt` — things to avoid
- `image` / `first_frame_image` / `start_image` — URL or local path for image-to-video

## Per-model schemas (common fields)

### bytedance/seedance-2.0

```json
{
  "prompt": "a sea turtle gliding over a coral reef at sunset, cinematic, 4k",
  "duration": 5,
  "resolution": "720p",
  "aspect_ratio": "16:9",
  "generate_audio": true,
  "image": "https://...",
  "last_frame_image": "https://...",
  "reference_images": [],
  "reference_videos": [],
  "reference_audios": [],
  "seed": 42
}
```

Notes: ByteDance's flagship multimodal video generator — one endpoint does T2V, I2V (`image`), first-last-frame morph (`image` + `last_frame_image`), reference-driven (up to 9 `reference_images`, 3 `reference_videos` ≤15s total, 3 `reference_audios` ≤15s total — cite positionally in the prompt as `[Image1]`/`[Video1]`/`[Audio1]`), all with **native synchronized audio on by default** (`generate_audio: true`; dialogue comes from `"double-quoted"` spans in the prompt). `duration` is 1–15s (`-1` for intelligent-duration), `resolution` is `480p`/`720p`/`1080p` (default `720p`), `aspect_ratio` is 8-way: `16:9`/`4:3`/`1:1`/`3:4`/`9:16`/`21:9`/`9:21`/`adaptive` (use `adaptive` for I2V to match the image). **`image`/`last_frame_image` are mutually exclusive with `reference_*` inputs.** **NOT present:** `negative_prompt`, `fps`, and any camera-control fields — camera movement is prompt-driven only (describe it: "slow dolly-in", "orbit shot"). Users coming from `minimax/video-01-director` will miss the bracketed `[Push in]`-style tags. **Pricing is not published** on the Replicate model page; as a calibration guess against `vidu/q3-pro` at 720p (~$0.15/s), expect order-of-magnitude ~$0.75 for 5s and ~$2.25 for 15s at 720p — **estimate only, verify in the playground**. Sibling `bytedance/seedance-2.0-fast` is a throughput-optimized variant on the same account — use for iteration, fall back to `seedance-2.0` for the final pass. Deep-dive: [bytedance/seedance-2.0](models/bytedance-seedance-2.0.md).

### runwayml/gen-4.5

```json
{
  "prompt": "...",
  "duration": 5,
  "aspect_ratio": "16:9",
  "seed": 42
}
```

Notes: premium tier. Excellent physics (weight, liquids, fabric). Deep-dive: [runwayml/gen-4.5](models/runwayml-gen-4.5.md).

### google/veo-3.1

```json
{
  "prompt": "...",
  "duration": 8,
  "aspect_ratio": "16:9",
  "negative_prompt": "blurry, low quality"
}
```

Notes: native audio. Check for `-fast` / `-lite` variants if latency or cost matters.

### kwaivgi/kling-v3-video

```json
{
  "prompt": "...",
  "duration": 10,
  "aspect_ratio": "16:9"
}
```

Notes: supports multi-shot mode (up to 6 connected scenes in one generation); lip-synced dialogue.

### kwaivgi/kling-v3-omni-video

Filed primarily as a **generation** model (T2V/I2V/reference-based) but also does prompt-driven video editing via `video_reference_type: "base"` — see the [Video editing](#video-editing) section for that usage.

```json
{
  "prompt": "<<<image_1>>> walks into a bustling night market",
  "mode": "pro",
  "duration": 6,
  "aspect_ratio": "9:16",
  "reference_images": ["./character.jpg"],
  "generate_audio": true
}
```

Notes: one endpoint, four workflows (T2V, I2V with optional last-frame, reference-based up to 7 images, video-edit); native audio is mutually exclusive with `reference_video`; iterate at `mode: "standard"` (720p) before promoting to `"pro"` (1080p). `pro` 15s runs take ~9 minutes. Deep-dive: [kwaivgi/kling-v3-omni-video](models/kwaivgi-kling-v3-omni-video.md).

### minimax/hailuo-2.3 (image-to-video)

```json
{
  "prompt": "camera pans left, character smiles",
  "first_frame_image": "https://... or /local/path.png",
  "duration": 6
}
```

Notes: also supports text-only; has `standard` and `pro` quality tiers.

### minimax/video-01-director

```json
{
  "prompt": "[Push in, Pan left] a lone samurai in a bamboo grove at dawn, mist curling around his feet",
  "prompt_optimizer": true
}
```

Notes: MiniMax Video-01 with an explicit **director mode** — recognises bracketed camera directives (`[Push in]`, `[Pan left]`, `[Zoom out]`, `[Tilt up]`, `[Tracking shot]`, etc.) and executes them as deterministic camera control. Up to 3 combined moves per bracket group. Fixed output: 720p, 25fps, up to 6s, no audio, no `seed`, no `duration` knob. Aspect ratio comes from `first_frame_image` (I2V) or defaults to 16:9 (T2V). Reach for this when you need a specific, repeatable camera move. Deep-dive: [minimax/video-01-director](models/minimax-video-01-director.md).

### wan-video/wan-2.7-t2v

```json
{
  "prompt": "...",
  "duration": 5,
  "aspect_ratio": "16:9",
  "seed": 42
}
```

Notes: open-source weights, 27B MoE. Look for `-fast` variants for iteration.

### wan-video/wan-2.7-i2v

```json
{
  "first_frame": "./landscape.jpg",
  "prompt": "slow dolly-in, clouds drift across the sky, leaves rustle",
  "duration": 5,
  "resolution": "1080p"
}
```

Notes: four modes share the endpoint — image-to-video, first-and-last-frame morph, clip continuation (`first_clip`), and audio-synchronized (pass `audio`). **Audio is generated by default** if you don't supply one — strip post-hoc with `ffmpeg -an` if you want silent output. `first_frame` and `first_clip` are mutually exclusive. Companion to `wan-video/wan-2.7-videoedit`. Deep-dive: [wan-video/wan-2.7-i2v](models/wan-video-wan-2.7-i2v.md).

### lightricks/ltx-video

```json
{
  "prompt": "A low-angle tracking shot gliding through a foggy pine forest at dawn. Shafts of golden sunlight cut between the trees. Dew glistens on the ferns. Cinematic, shallow depth of field, 4k, HDR.",
  "length": 97,
  "target_size": 640,
  "aspect_ratio": "3:2",
  "steps": 30,
  "cfg": 3
}
```

Notes: Lightricks' fast open-source DiT model — often faster than realtime on-GPU, ~$0.08/run, 24fps fixed. Uses `length` (frame count enum, 97–257, `8k+1`) and `target_size` (int enum 512–1024) instead of `duration`/`resolution`. **Needs long, descriptive prompts** — short prompts produce noticeably worse output. Max ~10.7s, no audio. Sweet spot: rapid iteration, batch sweeps, drafts before promoting to Seedance/Kling. Deep-dive: [lightricks/ltx-video](models/lightricks-ltx-video.md).

### vidu/q3-pro

```json
{
  "prompt": "...",
  "duration": 8,
  "resolution": "1080p",
  "aspect_ratio": "16:9",
  "audio": true
}
```

Notes: three modes in one endpoint — text-to-video, image-to-video (`start_image`), and start-end-to-video (`start_image` + `end_image`, ratios must match within 0.8–1.25). Up to 16s at 1080p with synced dialogue/SFX. 540p at $0.07/s is a cheap draft tier. Text rendering inside video is unreliable. Deep-dive: [vidu/q3-pro](models/vidu-q3-pro.md).

### pixverse/pixverse-v6

```json
{
  "prompt": "...",
  "quality": "540p",
  "duration": 5,
  "aspect_ratio": "16:9"
}
```

Notes: PixVerse's flagship — cheap, fast T2V/I2V with optional native audio via `generate_audio_switch`, multi-shot via `generate_multi_clip_switch`, and first-last-frame transition (`image` + `last_frame_image`). Billed per second, from $0.05/s (360p) to $0.23/s (1080p + audio). `duration` is a fixed enum `5|8|10|15`. Supersedes v5.6 for new work (better camera control, in-frame text, multi-shot, first-person POV). Deep-dive: [pixverse/pixverse-v6](models/pixverse-pixverse-v6.md).

### pixverse/pixverse-v5.6

```json
{
  "prompt": "...",
  "duration": 5,
  "aspect_ratio": "16:9"
}
```

Notes: unit-based pricing. Kept here for back-compat — prefer v6 for new work.

### pixverse/pixverse-v5

```json
{
  "prompt": "A young woman in a bright yellow sundress on a sunlit rooftop",
  "effect": "Let's YMCA!",
  "quality": "540p",
  "duration": 5,
  "aspect_ratio": "9:16"
}
```

Notes: **v6 supersedes v5 for normal work.** The only real reason to pick v5 is its **15-value `effect` enum** (v6 removed the field): `None`, `Let's YMCA!`, `Subject 3 Fever`, `Ghibli Live!`, `Suit Swagger`, `Muscle Surge`, `360° Microwave`, `Warmth of Jesus`, `Emergency Beat`, `Anything, Robot`, `Kungfu Club`, `Mint in Box`, `Retro Anime Pop`, `Vogue Walk`, `Mega Dive`, `Evil Trigger`. Also supports T2V, I2V (via `image`), and first-last-frame transitions (`image` + `last_frame_image`; `effect` must be `"None"` for transitions). `duration` is enum `5|8` only (v6 adds `10|15`). `quality: "1080p"` is **only valid at `duration: 8`** (v6 removes that restriction). **No `generate_audio_switch`** (v5 is silent) and **no `generate_multi_clip_switch`** (single-shot only). Billing is **unit-based, not $/second** — 1080p = 80 base units, 8s = 2× multiplier (so 1080p-8s = 160 units); see model-page footer for the $/unit rate. v6's per-second 540p ($0.07/s) is competitive with v5's cheap tier — v5 is **not** meaningfully cheaper as a draft. Deep-dive: [pixverse/pixverse-v5](models/pixverse-pixverse-v5.md).

### prunaai/p-video

```json
{
  "prompt": "a neon-lit tokyo alley with steam rising from a ramen stall",
  "duration": 5,
  "resolution": "720p",
  "draft": true
}
```

Notes: Pruna's fast, cheap generator — handles T2V, I2V (`image`), start-end (`image` + `last_frame_image`), and audio-driven (`audio`, which ignores `duration`). **Draft mode** is 4× faster and 4× cheaper (`$0.005/s` at 720p, ~$0.025 for a 5s clip) — among the cheapest on Replicate. Default at 720p normal is $0.02/s. Gotcha: `disable_safety_filter` defaults to **`true`** (filter OFF) — flip to `false` if you need safety checks. Deep-dive: [prunaai/p-video](models/prunaai-p-video.md).

## Video editing

Prompt-driven modification of an existing video clip (background swap, relighting, style transfer, outfit change) while preserving underlying motion.

### wan-video/wan-2.7-videoedit

```json
{
  "video": "./source.mp4",
  "prompt": "replace the background with a sunlit beach and gentle waves, keep the subject unchanged",
  "resolution": "1080p",
  "audio_setting": "origin"
}
```

Notes: natural-language editing over an existing clip. Good at background swap, lighting shifts, style transfer, clothing tweaks. Sweet spot is 2–5s (2–10s hard range). Pass `reference_image` when you have a concrete visual target — beats trying to describe "make it look like [film]". `audio_setting: "origin"` keeps source audio verbatim (use for talking heads to avoid lip drift); `"auto"` lets the model regenerate. Struggles with spatial rearrangement, detailed facial changes, and physics-based edits. Deep-dive: [wan-video/wan-2.7-videoedit](models/wan-video-wan-2.7-videoedit.md).

### kwaivgi/kling-v3-omni-video (video-edit mode)

Cross-reference — same model listed above under generation, but it also does prompt-driven video editing:

```json
{
  "prompt": "repaint this scene in the style of a Studio Ghibli film, soft watercolor background",
  "reference_video": "./clip.mp4",
  "video_reference_type": "base",
  "keep_original_sound": true
}
```

Notes: set `video_reference_type: "base"` to edit the reference video. `duration` is ignored (output matches reference length). Reference video must be 3–10s, ≤200MB. `generate_audio` is mutually exclusive with `reference_video`. Pick this over `wan-2.7-videoedit` when you want reference-image-driven edits in combination with character consistency. Deep-dive: [kwaivgi/kling-v3-omni-video](models/kwaivgi-kling-v3-omni-video.md).

## Motion / expression transfer

Drive a still image's performance from a reference video — different beast from T2V or I2V.

### bytedance/dreamactor-m2.0

```json
{
  "image": "./portrait.jpg",
  "video": "./actor_performance.mp4"
}
```

Notes: motion + expression + lip transfer. Give it a single subject image (human, cartoon, animal, non-humanoid — learns from raw pixels, no skeletal pose estimation) and a driving video up to 30s; output re-animates the subject with the driving clip's motion and facial performance. Use for "bring this portrait to life" or retargeting a performance onto a different character. `cut_first_second: true` (default) trims a 1-second startup transition. For **audio-driven** lipsync (no driving video) use `heygen/lipsync-speed` or `zsxkib/multitalk` instead. Deep-dive: [bytedance/dreamactor-m2.0](models/bytedance-dreamactor-m2.0.md).

## Lipsync

Replace / drive mouth motion on an existing video using audio.

### heygen/lipsync-speed

```json
{
  "video": "https://example.com/speaker.mp4",
  "audio": "./voiceover-es.wav",
  "enable_dynamic_duration": true,
  "enable_speech_enhancement": true
}
```

Notes: audio-driven lipsync — takes a source video + replacement audio and re-animates the speaker's mouth. Optimized for **speed** ($0.0333/s of output, ~$2 for 60s). Use for dubbing, voiceover replacement, localization, ADR. For higher fidelity close-ups, upgrade to `heygen/lipsync-precision`. Default to speed; upgrade only if output isn't good enough. Deep-dive: [heygen/lipsync-speed](models/heygen-lipsync-speed.md).

### zsxkib/multitalk

```json
{
  "image": "./two_hosts_at_mics.jpg",
  "first_audio": "./host_a.wav",
  "second_audio": "./host_b.wav",
  "prompt": "two podcast hosts having a lively discussion, making eye contact, natural gestures",
  "num_frames": 121
}
```

Notes: **audio-driven multi-person conversational video** — takes one reference image containing one or two people plus per-person audio tracks, and produces a video where each subject lip-syncs their own audio while the model handles turn-taking, reactions, and eye contact. Think podcast-style two-shot from a still + two voiceovers. Max 2 people, ~8s hard cap (`num_frames` 25–201, snaps to `4n+1`). ~$0.59/run, ~7 min runtime. Omit `second_audio` for single-person talking head. Deep-dive: [zsxkib/multitalk](models/zsxkib-multitalk.md).

## Aspect-ratio change / outpaint

### luma/reframe-video

Common inputs: `video` (local upload) OR `video_url`; `aspect_ratio` enum `1:1`/`3:4`/`4:3`/`9:16`/`16:9`/`9:21`/`21:9` (default `16:9`); optional `prompt` to steer the invented content; optional crop-bounds (`x_start`/`y_start`/`x_end`/`y_end`) and `grid_position_x/y` for off-center placement.

Notes: Luma's **generative reframe** — the correct tool for "make this video a different aspect ratio." It _invents_ new, temporally-coherent content on the extended sides (people, backdrop, props), not a crop, blur-bar, or stretch. **Input max 10s; output is 720p** at the chosen aspect. Leave the crop/grid params default for a simple centered reframe (original stays centered, model fills the new margins). A light `prompt` describing the _backdrop_ steers the fill without forcing new subjects — keep it scene-descriptive to avoid hallucinating extra people. Frequent shot cuts in the source actually help (less runway for drift); the real failure mode is morph/flicker within one long continuous shot, so spot-check invented regions across the clip. ~$0.25–0.35 for 10s (metered), ~2 min runtime. Beats the ffmpeg blur-fill cheat when you want it to look natively shot at the target ratio; blur-fill still wins on speed/cost and gives 1080p. **NOT the tool for:** flow-based content-completion/object-removal (that's ProPainter — but note `jd7h/propainter` was erroring on Replicate as of 2026-07). Verify pricing in the playground: <https://replicate.com/luma/reframe-video>.

## Matting / background removal

### arielreplicate/robust_video_matting

```json
{
  "input_video": "./person_talking.mp4",
  "output_type": "green-screen"
}
```

Notes: Robust Video Matting (RVM) — extracts the foreground from a video with a recurrent network for temporal stability (no background reference needed). **Trained for people** — animals/objects less reliable. `output_type` options: `green-screen` (chroma-key ready, most compatible), `alpha-mask` (grayscale matte), `foreground-mask` (subject with transparency, cleanest for programmatic compositing). ~$0.034 flat per run, ~35s runtime — cheap enough to run as a default preprocessing step. Supports up to 4K. Deep-dive: [arielreplicate/robust_video_matting](models/arielreplicate-robust_video_matting.md).

## Colorization

### arielreplicate/deoldify_video

```json
{
  "input_video": "./old_home_movie.mp4",
  "render_factor": 21
}
```

Notes: DeOldify Video — automatic colorization of B&W footage with built-in temporal stabilization. Sweet spot: archival/historical footage, home movies, old film reels where "believable, warm, filmic palette" is the goal. **Known warm/sepia/orange bias** — skip for precision work (brand colors, historically accurate uniforms). `render_factor`: lower (~10–15) = faster, more vibrant, lower-res color layer (good for grainy early-1900s); higher (~30–40) = finer detail but can wash out. Default is **21** (schema description says 35, but the real default is 21 — set explicitly). ~$0.11 per run but runtime scales with frames — default example ran ~25 min; chunk clips longer than a few minutes and concat with `ffmpeg`. Deep-dive: [arielreplicate/deoldify_video](models/arielreplicate-deoldify_video.md).

## Face restoration

Temporally-stable face restoration on video clips — different problem from running an image-domain face restorer frame-by-frame (which flickers).

### zsxkib/stable-video-face-restoration

```json
{
  "video": "./lowres_interview.mp4",
  "tasks": "face-restoration",
  "num_inference_steps": 30,
  "overlap": 3,
  "decode_chunk_size": 16,
  "min_appearance_guidance_scale": 2,
  "max_appearance_guidance_scale": 2
}
```

Notes: SVFR ("Stable Video Face Restoration") — a Stable-Video-Diffusion-style backbone conditioned on per-frame face priors for **temporal stability** through motion, so restored faces don't flicker/boil frame-to-frame the way per-frame CodeFormer/GFPGAN do. One endpoint, three modes via `tasks` enum: `face-restoration`, `face-restoration-and-colorization`, or `face-restoration-and-colorization-and-inpainting` (latter requires `mask`). **No CodeFormer-style fidelity knob** — identity-vs-restoration balance goes through `min_appearance_guidance_scale` / `max_appearance_guidance_scale` (both default **2**); raise both for stronger restoration, lower both for gentler. `overlap` (default **3**) controls temporal smoothing across segment boundaries; `decode_chunk_size` (default 16) is the OOM-avoidance knob on long clips. **Single front-facing subject is the sweet spot** — multi-face behavior is not documented in the schema; test on a short segment if your footage has multiple people. Runtime scales **linearly with frame count × steps** (~2 s/frame at 30 steps on L40S) — a 30 fps 30 s clip ≈ 30+ minutes, near Replicate's default timeout. Chunk long video at ~20 s and concat with `ffmpeg`; reuse the same `seed` for consistency. **Audio is not preserved** — mux back afterward. License: **non-commercial research only** per upstream SVFR. **Pricing not published as a flat per-run number** — check the playground estimator at <https://replicate.com/zsxkib/stable-video-face-restoration>. For **image-domain** face restoration (stills, thumbnails, single-frame extractions), use `sczhou/codeformer` or `tencentarc/gfpgan` instead — 5–100× cheaper per frame, they expose the explicit fidelity dial, and they handle multi-face images cleanly (see [image-models.md](image-models.md)). Deep-dive: [zsxkib/stable-video-face-restoration](models/zsxkib-stable-video-face-restoration.md).

## Cost awareness

Video generation costs real money per call. Rough ranges (confirm on <https://replicate.com/><model>):

- Pruna p-video draft, LTX: ~$0.025–$0.10 per clip (cheapest tier)
- Pixverse v6 draft/540p, Wan-fast, Grok: ~$0.05–$0.40 per clip
- Pixverse v5 (unit-billed, not $/s): ~$0.15–$0.50 per clip depending on `quality` × `duration` (1080p-8s = 160 units is the priciest v5 combo — convert with the current $/unit rate in the model page footer)
- Seedance, Minimax, Vidu q3-pro 720p: ~$0.20–$0.80
- Kling (omni, v3), Veo, Pixverse v6 1080p+audio: ~$0.40–$3.50
- Runway gen-4.5: ~$0.50–$1.50+

Post-processing / editing / lipsync / matting are usually cheaper:

- Robust video matting: ~$0.034/run flat
- DeOldify video: ~$0.11/run (scales with runtime)
- Heygen lipsync-speed: ~$0.033/s of output
- Multitalk: ~$0.59/run
- Stable video face restoration: **not published on the model page — scales linearly with frame count × steps on L40S; roughly ~$0.05–$0.25 for a short clip (few seconds), much more for long clips.** Verify in the playground estimator.

Tell the user which model you're about to run before kicking off anything above ~$0.30 unless they explicitly picked the model.
