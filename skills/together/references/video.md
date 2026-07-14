# Together — video generation

> **Script:** `scripts/video.py "prompt" -o out.mp4` handles the full submit→poll→download→embed flow.

Generate video from a text prompt (and optionally image/video inputs). **Asynchronous and on a different API version:** you `POST` a job to **`/v2/videos`**, get a job `id` back with `status: "in_progress"`, then poll `GET /v2/videos/{id}` until `status` is `completed` and download `outputs.video_url`.

> **Heads up:** this is the only part of the skill on **`/v2`**, not `/v1`. Same host and auth.

Remember the **provenance rule** in `references/provenance.md` — once you download the mp4, embed the model slug + prompt with `exiftool`.

## Submit a job

```bash
curl -sS https://api.together.ai/v2/videos \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ByteDance/Seedance-1.0-lite",
    "prompt": "A cartoon astronaut riding a horse on the moon, slow dolly-in",
    "seconds": "5",
    "ratio": "16:9"
  }' | jq '{id, status}'
```

```json
{ "id": "video-abc123xyz", "status": "in_progress" }
```

## Poll until done

```bash
curl -sS https://api.together.ai/v2/videos/video-abc123xyz \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  | jq '{status, url: .outputs.video_url, cost: .outputs.cost}'
```

`status` walks `in_progress` → `completed` (or `failed`). On completion the result lands at `outputs.video_url`:

```json
{
  "id": "video-abc123xyz",
  "object": "video",
  "model": "ByteDance/Seedance-1.0-lite",
  "status": "completed",
  "created_at": 1704067200,
  "completed_at": 1704067320,
  "size": "1280x720",
  "seconds": "5",
  "outputs": {
    "cost": 14,
    "video_url": "https://videos.together.ai/.../video-abc123xyz.mp4"
  }
}
```

On failure, `status` is `failed` and `error` holds `{ code, message }`.

### Submit → poll → download, end to end

```bash
ID=$(curl -sS https://api.together.ai/v2/videos \
  -H "Authorization: Bearer $TOGETHER_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"ByteDance/Seedance-1.0-lite","prompt":"neon koi swimming through fog","seconds":"5"}' \
  | jq -r '.id')

while :; do
  STATUS=$(curl -sS https://api.together.ai/v2/videos/$ID \
    -H "Authorization: Bearer $TOGETHER_API_KEY")
  S=$(echo "$STATUS" | jq -r '.status')
  echo "status: $S"
  [ "$S" = "completed" ] && echo "$STATUS" | jq -r '.outputs.video_url' && break
  [ "$S" = "failed" ] && echo "$STATUS" | jq '.error' && break
  sleep 5
done
```

## Request body

| Field             | Type    | Notes                                                                                                                                          |
| ----------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `model`           | string  | **Required.** Model slug — see table below                                                                                                     |
| `prompt`          | string  | Text description (1–32000 chars)                                                                                                               |
| `negative_prompt` | string  | Content to exclude                                                                                                                             |
| `seconds`         | string  | Clip duration, as a string (e.g. `"5"`)                                                                                                        |
| `ratio`           | string  | Aspect ratio (e.g. `"16:9"`)                                                                                                                   |
| `resolution`      | string  | Resolution spec; or set `width`/`height` explicitly                                                                                            |
| `width`/`height`  | integer | Output dimensions in px                                                                                                                        |
| `fps`             | integer | Frames per second (default 24)                                                                                                                 |
| `steps`           | integer | Denoising steps, 10–50 (quality/speed tradeoff)                                                                                                |
| `seed`            | integer | Deterministic seed                                                                                                                             |
| `guidance_scale`  | number  | Prompt adherence; ~6–10 recommended                                                                                                            |
| `output_format`   | string  | `MP4` (default) or `WEBM`                                                                                                                      |
| `generate_audio`  | boolean | Synthesize audio (model-dependent; e.g. Veo "audio" variants)                                                                                  |
| `media`           | object  | Image/video inputs: `frame_images`, `reference_images`, `source_video`, etc. — for image-to-video, keyframing, and reference-guided generation |

Not every model honors every field — confirm per-model behavior when picking one.

## Models (pricing is per-video, flat)

Together hosts 30+ video models; pick by budget and provider. A representative spread:

| Model slug                    | $/video | Notes                      |
| ----------------------------- | ------- | -------------------------- |
| `ByteDance/Seedance-1.0-lite` | $0.14   | Cheap, solid default       |
| `ByteDance/Seedance-1.0-pro`  | $0.57   | Higher quality Seedance    |
| `minimax/hailuo-02`           | $0.49   | Strong motion              |
| `kwaivgI/kling-2.1-standard`  | $0.18   | Budget Kling               |
| `kwaivgI/kling-2.1-pro`       | $0.32   | Better Kling               |
| `Wan-AI/Wan2.2-T2V-A14B`      | $0.66   | Text-to-video              |
| `Wan-AI/Wan2.2-I2V-A14B`      | $0.31   | Image-to-video             |
| `google/veo-3.0-fast`         | $0.80   | Google Veo, faster tier    |
| `google/veo-3.0-audio`        | $3.20   | Veo with synthesized audio |
| `openai/sora-2`               | $0.80   | OpenAI Sora 2              |
| `openai/sora-2-pro`           | $2.40   | Sora 2 pro tier            |

Full current list + prices: `GET /v1/models` (filter for video) or the Together pricing page. Slugs and prices drift, and some catalog entries are test/debug — verify before wiring one into anything durable.

## Notes

- Base path is **`/v2`** for video; everything else in this skill is `/v1`.
- It's async — always poll; the submit call does **not** block until the video is ready.
- Cost comes back in `outputs.cost` on the completed job.
