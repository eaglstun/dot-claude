# Kling v2.1 I2V Pro

Part of the [Public Endpoint models index](README.md).

`model-id`: `kling-v2-1-i2v-pro` — **❌ docs only, not independently verified.** Image-to-video — requires a source `image` URL, not text-to-video.

Pricing per docs: $0.45 per 5s, $0.90 per 10s.

```json
// request
{
  "input": {
    "prompt": "A majestic magic dragon breathing fire over an ancient castle",
    "image": "https://example.com/dragon.png",
    "negative_prompt": "",
    "guidance_scale": 0.5,
    "duration": 5,
    "enable_safety_checker": true
  }
}
// documented response (NOT independently confirmed)
{"output":{"video_url":"https://video.runpod.ai/abc123/output.mp4","cost":0.36},"status":"COMPLETED"}
```

Doc's example `executionTime` was ~68s for a 5s clip — expect this to be a `/run` + poll workload in practice, not a comfortable `/runsync` call (see the `/runsync` doesn't-always-block gotcha in [`../data-plane.md`](../data-plane.md)).

## Sources

docs.runpod.io/public-endpoints/models/kling-v2-1 — not live-tested.
