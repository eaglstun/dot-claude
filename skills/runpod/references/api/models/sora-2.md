# SORA 2 I2V

Part of the [Public Endpoint models index](README.md).

`model-id`: `sora-2-i2v` — **❌ docs only, not independently verified.** Image-to-video, `duration` in seconds (4/8/12 are the priced tiers).

Pricing per docs: $0.40 (4s), $0.80 (8s), $1.20 (12s). A "SORA 2 Pro I2V" variant also exists per the catalog table (from $1.20 at 720p/4s) — not documented here, presumably a different `model-id`.

```json
// request
{
  "input": {
    "prompt": "Action: The mech slowly pushes itself up with a damaged mechanical arm, sparks flying. Ambient Sound: Distant explosions, electrical sizzle. Character Dialogue: (Processed mechanical voice) No retreat.",
    "image": "https://example.com/mech.jpeg",
    "duration": 4
  }
}
// documented response (NOT independently confirmed)
{"output":{"video_url":"https://video.runpod.ai/abc123/output.mp4","cost":0.40},"status":"COMPLETED"}
```

Doc's example `executionTime` was ~120s for a 4s clip — definitely a `/run` + poll workload, not `/runsync` (see [`../data-plane.md`](../data-plane.md)).

## Sources

docs.runpod.io/public-endpoints/models/sora-2 — not live-tested.
