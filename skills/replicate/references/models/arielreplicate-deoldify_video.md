# arielreplicate/deoldify_video

Model page: <https://replicate.com/arielreplicate/deoldify_video>

**DeOldify Video** — colorizes black-and-white video by running the classic DeOldify deep-colorization model frame-by-frame with built-in temporal stabilization. The sweet spot is **archival/historical footage, home movies, and old film reels** where the goal is a believable, warm, filmic palette rather than ground-truth-accurate color. Fully automatic: no per-shot color guidance, no reference images — you feed a video in, a colorized MP4 comes out.

## When to pick this model

- **Pick it** for old archival footage, silent film, home-movie reels, WWII-era clips, any B&W video where "fast, automatic, mostly plausible color" is the bar. Temporal stabilization keeps colors from flickering frame-to-frame — a major upgrade over running image DeOldify per frame.
- **Skip it** if you need _accurate_ colorization (brand colors, historically precise uniforms/flags, known skin tones) — DeOldify has a known warm/sepia/orange palette bias and can't be steered. For precision work, color-grade manually or use a reference-guided colorization tool.
- **Skip it** for long videos (10+ min). Runtime scales linearly with frames — default example was ~25 minutes of compute for a short Chaplin clip. Chunk long inputs and concat with `ffmpeg`.
- **Skip it** if you were going to run image DeOldify per frame — this model is the better choice (same colorizer, plus temporal stabilization, plus it's set up for video I/O).

## Input schema

| Field           | Type         | Required | Default | Description                                                                                                                |
| --------------- | ------------ | -------- | ------- | -------------------------------------------------------------------------------------------------------------------------- |
| `input_video`   | string (URI) | yes      | —       | Path or URL to the B&W (or faded-color) video to colorize. Local paths are auto-uploaded by `run_model.py`.                |
| `render_factor` | integer      |          | `21`    | Resolution at which the color layer is rendered. Lower = faster + more vibrant colors, higher = more detail but may wash out. Typical usable range ~10–40. |

Note on `render_factor`: the schema description mentions `35` as a "carefully chosen" default, but the schema's actual `default` is **`21`** — that's what you get if you omit the field.

## Output

A single URI to the colorized MP4. Saved as `arielreplicate_deoldify_video_0.mp4`.

## Pricing and runtime

- **~$0.11 per run** (flat, but "varies depending on your inputs" — i.e. video length and render_factor drive compute time)
- Runs on **Nvidia T4 GPU**
- Typical runtime **~8 minutes** per the model page; the default example in the schema ran in **~1544 seconds (~25.7 minutes)** at `render_factor: 21` on a short Chaplin clip — so budget generously for longer inputs.
- No documented max-duration limit, but Replicate's default prediction timeout plus T4 memory mean **long videos (5+ minutes) are risky** — chunk and concat.

## Examples

**Basic colorization (default render_factor = 21):**

```bash
python scripts/run_model.py arielreplicate/deoldify_video \
    --input '{"input_video": "./old_home_movie.mp4"}' \
    --output ./out/
```

**Higher detail for period film (HD/2K scans):**

```bash
python scripts/run_model.py arielreplicate/deoldify_video \
    --input '{
      "input_video": "./restored_1940s_reel.mp4",
      "render_factor": 35
    }' \
    --output ./out/
```

**More vibrant, faster render for low-quality archival footage:**

```bash
python scripts/run_model.py arielreplicate/deoldify_video \
    --input '{
      "input_video": "./grainy_8mm_clip.mp4",
      "render_factor": 12
    }' \
    --output ./out/
```

### Render_factor tradeoff cheat-sheet

| Value   | Behavior                                                              | Best for                                              |
| ------- | --------------------------------------------------------------------- | ----------------------------------------------------- |
| ~10–15  | Fast, **more vibrant/saturated** colors, color layer is lower-res     | Low-quality / grainy / early-1900s footage            |
| ~21     | Default balance                                                       | Generic archival video, unsure where to start         |
| ~30–40  | Slower, **finer color detail** but colors can look slightly washed    | Clean HD scans of later-era B&W film (1950s–60s)      |

If colors look flat/dull, _lower_ `render_factor`. If colors bleed across edges or look blobby, _raise_ it.

## Strengths / gotchas

**Good at:**

- Automatic, zero-config colorization of old video.
- **Temporal stability** — the model bakes in frame-to-frame consistency so colors don't strobe/flicker the way naive per-frame image colorization does.
- Faces, skin tones, foliage, and skies in well-lit daytime footage.
- Early-cinema / silent-film aesthetic — the sepia-leaning palette is actually on-brand here.

**Gotchas:**

- **Warm/orange/sepia palette bias.** DeOldify tends to push skin and earth tones orange and can under-saturate blues and greens. This is baked into the training — there's no parameter to correct it. Post-grade if you need a cooler look.
- **Runtime scales with frames.** A 1-minute clip can take 15+ minutes on T4; a 5-minute clip can push 60+ minutes and risk timeouts. **Chunk long videos** (e.g. 30–60 sec segments) and concatenate with `ffmpeg` afterward.
- **Fast cuts break temporal stabilization.** At shot boundaries the model can briefly flip color choices (a coat goes brown, then blue, then brown). Pre-split long videos on cuts, colorize each shot independently, re-assemble.
- **Low-light, foggy, or high-contrast scenes** confuse the colorizer — expect muddy or gray-leaning output in night/interior/snow scenes.
- **No audio preservation guarantees** — the pipeline is video-frames-focused. If your output is silent or has odd audio, mux the original audio back in with `ffmpeg -i colorized.mp4 -i original.mp4 -map 0:v -map 1:a -c copy out.mp4`.
- **`render_factor` schema description mentions 35 as "default"** but the actual default is **21**. Set it explicitly if you care — don't trust the prose.
- **Input codec quirks.** Obscure containers/codecs may fail; re-encode to standard H.264 MP4 first if you hit a decode error.
- GitHub / license: <https://github.com/ArielReplicate/DeOldify> — forked from the original DeOldify project (<https://github.com/jantic/DeOldify>, MIT). Verify the license for commercial use.
