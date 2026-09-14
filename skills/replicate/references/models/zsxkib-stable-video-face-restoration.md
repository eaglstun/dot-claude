# zsxkib/stable-video-face-restoration

Model page: <https://replicate.com/zsxkib/stable-video-face-restoration>

**SVFR** ("A Unified Framework for Generalized Video Face Restoration") — video-domain face restoration with **built-in temporal stability**. A Stable-Video-Diffusion-style video backbone is conditioned on per-frame face priors so the restored face stays consistent across frames instead of flickering. One model, three modes via a `tasks` switch: restoration only, restoration + colorization, or restoration + colorization + inpainting (mask-driven). Upstream paper + code: <https://github.com/wangzhiyaoo/SVFR>. Replicate fork: <https://github.com/zsxkib/SVFR/tree/replicate>.

## When to pick this over image-domain face restorers

- **Pick SVFR over running `sczhou/codeformer` or `tencentarc/gfpgan` frame-by-frame** on video. Per-frame image restoration has zero temporal awareness: eyes, mouth corners, skin texture, and identity drift independently on every frame, producing a hallmark "boiling face" flicker. SVFR's video diffusion backbone enforces cross-frame consistency via segment overlap, so the restored identity is stable through motion.
- **Pick `sczhou/codeformer` or `tencentarc/gfpgan` instead** for stills, thumbnails, or single-frame extractions — they are 5–100x cheaper per frame, support the explicit `codeformer_fidelity` identity-vs-restoration knob (SVFR does not expose that directly), and handle multi-face images cleanly in a single pass.
- **Sweet spot for SVFR:** short clips (seconds to ~1 min) of degraded front-facing faces — compressed webcam recordings, old-home-video faces, low-bitrate interview clips, AI-generated talking-head footage with per-frame artifacts, vintage colorization-plus-restoration jobs.
- **Bonus capabilities vs the image siblings:** optional per-clip **colorization** (B&W → color in the same pass) and **mask-driven video inpainting** of the face region — neither is available in CodeFormer/GFPGAN.

## Input schema

| Field                           | Type          | Required | Default              | Description                                                                                                                                     |
| ------------------------------- | ------------- | -------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `video`                         | string (URI)  | yes      | —                    | Input video file (e.g. MP4). Local paths are auto-uploaded by `run_model.py`.                                                                   |
| `tasks`                         | enum (string) |          | `"face-restoration"` | One of `"face-restoration"`, `"face-restoration-and-colorization"`, `"face-restoration-and-colorization-and-inpainting"`.                       |
| `mask`                          | string (URI)  |          | —                    | Inpainting mask image (white = restore). **Only used** when `tasks` includes inpainting.                                                        |
| `num_inference_steps`           | integer       |          | `30`                 | Diffusion steps per clip. Higher = cleaner output but linearly slower.                                                                          |
| `decode_chunk_size`             | integer       |          | `16`                 | Frames per decoding chunk. Lowering reduces peak VRAM on long clips; raising speeds up short clips. Main knob for OOM avoidance.                |
| `overlap`                       | integer       |          | `3`                  | Overlapping frames between consecutive clip segments. Higher = smoother temporal consistency across segment boundaries, slower overall.         |
| `noise_aug_strength`            | number        |          | `0`                  | Noise augmentation applied to conditioning frames. Small positive values can help when input is very noisy; default `0` for clean(ish) inputs.  |
| `min_appearance_guidance_scale` | number        |          | `2`                  | Lower bound of appearance (restoration) guidance scale used within a clip — roughly the "how strongly push toward a clean face" knob, floor.    |
| `max_appearance_guidance_scale` | number        |          | `2`                  | Upper bound of appearance guidance scale — ceiling. Raising both pushes harder restoration (at some identity cost); lowering stays gentler.     |
| `i2i_noise_strength`            | number        |          | `1`                  | Image-to-image noise strength (how much the diffusion trajectory is reset from the source frames). `1` = full denoise trajectory.               |
| `seed`                          | integer       |          | random               | Random seed. Leave blank to randomize; set for reproducible runs.                                                                               |

Notes on the guidance knobs: SVFR does **not** expose a direct CodeFormer-style `codeformer_fidelity` / `w` parameter. The closest lever is the `min_appearance_guidance_scale` / `max_appearance_guidance_scale` pair — raising both = more aggressive restoration (stronger push toward the clean-face prior), lowering both = gentler restoration (more faithful to the original frames). Defaults (`2` / `2`) are the documented sweet spot; change in small increments (±0.5–1.0).

## Output

A single URI to the restored MP4. Saved as `zsxkib_stable-video-face-restoration_0.mp4`.

## Pricing and runtime

- Runs on **Nvidia L40S GPU** hardware. Replicate had not published a flat per-run price on the model page at time of writing — **check the playground price estimator at <https://replicate.com/zsxkib/stable-video-face-restoration> before batching**. Based on L40S billing rates and the default-example timing, expect roughly **$0.05–$0.25 per short clip** (a few seconds of video), scaling linearly with frame count and `num_inference_steps`.
- Default example on the model page: a **54-frame** clip with `face-restoration-and-colorization` completed in **~107 seconds of predict time** (~331s total including upload/queueing) on L40S. That's roughly **2s of compute per output frame** at 30 steps.
- **Runtime scales ~linearly with video length** (frame count) and with `num_inference_steps`. A 30 fps 30-second clip = ~900 frames ≈ **30+ minutes of compute** at defaults — near the edge of Replicate's default prediction timeout. Chunk inputs above ~20 seconds and concatenate with `ffmpeg` afterward.
- License: **non-commercial research use only** per upstream SVFR. Verify at <https://github.com/wangzhiyaoo/SVFR?tab=readme-ov-file#license> before any client work.

## Examples

**Basic video face restoration** (defaults — pure restoration, no colorization):

```bash
python scripts/run_model.py zsxkib/stable-video-face-restoration \
    --input '{
      "video": "./lowres_interview.mp4"
    }' \
    --output ./out/
```

**Restore + colorize a B&W clip** in one pass (replaces a CodeFormer-then-DeOldify pipeline):

```bash
python scripts/run_model.py zsxkib/stable-video-face-restoration \
    --input '{
      "video": "./old_home_movie.mp4",
      "tasks": "face-restoration-and-colorization",
      "num_inference_steps": 30,
      "seed": 42
    }' \
    --output ./out/
```

**Masked inpainting + restoration** for a clip with a damaged/occluded face region (white mask pixels = area to rebuild):

```bash
python scripts/run_model.py zsxkib/stable-video-face-restoration \
    --input '{
      "video": "./damaged_clip.mp4",
      "tasks": "face-restoration-and-colorization-and-inpainting",
      "mask": "./face_mask.png",
      "overlap": 5,
      "decode_chunk_size": 8
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- **Temporal stability on faces.** The video diffusion backbone + overlapping clip segments (`overlap`) produce noticeably less frame-to-frame flicker than per-frame CodeFormer/GFPGAN — the main reason to use this model at all.
- **Unified restoration + colorization + inpainting** in one pass via the `tasks` enum — no need to chain separate models.
- **Front-facing talking-head footage** with moderate degradation (compression, low resolution, noise). Matches the training distribution closely.

**Gotchas:**

- **No explicit CodeFormer-style fidelity/identity knob.** There is no `codeformer_fidelity` parameter; identity-vs-restoration balance is controlled indirectly via `min_appearance_guidance_scale` / `max_appearance_guidance_scale` (raise to push harder toward "clean face" prior, lower to stay closer to input). Less surgical than CodeFormer's single `w` parameter — do side-by-side sweeps on a short segment before committing to a long batch.
- **Runtime scales linearly with frames.** Default-example math: ~2s/frame at 30 steps on L40S. A 10s 30fps clip ≈ 10 min; a 60s 30fps clip ≈ 60 min — right at Replicate's default timeout. **Chunk long videos** into ~20s segments, run independently (same `seed` for consistency), concat with `ffmpeg`.
- **Memory risk on long / high-res clips.** `decode_chunk_size` (default `16`) is the main knob if the job OOMs — drop to `8` or `4`. Lower is safer but slower.
- **Multi-face handling is not a documented strength.** SVFR is built around a single front-facing subject per clip; it does not expose per-face tracking or independent identity locking for multiple subjects in the frame. Scenes with several faces may restore each face independently without the per-identity tracking that a dedicated face-tracker + CodeFormer pipeline would give. Test first on a short segment if your footage has multiple people.
- **Occlusion / side profiles / extreme angles degrade quality.** The model expects "clear, front-facing" faces per the upstream description. Heavy hair occlusion, hands over mouth, fast rotation to profile, or off-axis angles can cause the restoration to hallucinate or blur the occluded frames. Use the inpainting mode with an explicit mask if you have a known damaged region.
- **Face-detection failure modes:** if the detector loses the face mid-clip (motion blur, lighting change, hard cut), the corresponding frames may pass through largely unrestored or with temporal artifacts at the re-acquisition boundary. Cut on shot boundaries before running — never feed a multi-shot edit as a single clip.
- **Audio is not preserved** by the pipeline — output is video-only MP4. Mux original audio back in afterward: `ffmpeg -i svfr_out.mp4 -i original.mp4 -map 0:v -map 1:a -c copy final.mp4`.
- **`mask` is only consumed when `tasks` includes `inpainting`** — supplying a mask in restoration-only mode is a silent no-op.
- **License is non-commercial research only** (upstream SVFR). Do not use for client/commercial deliverables without written permission — unlike CodeFormer (NTU S-Lab 1.0) or GFPGAN (Apache 2.0), which have more permissive (though still restricted) terms.
