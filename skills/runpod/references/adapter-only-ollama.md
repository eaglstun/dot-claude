# Adapter-only Ollama updates

Use this path when a Runpod network volume can retain a shared base model and training rounds differ only by a LoRA adapter. The goal is to upload tens of megabytes per round rather than another fused GGUF.

## Preconditions

- Ollama can attach a GGUF LoRA with `FROM <base>` plus `ADAPTER <adapter.gguf>`.
- The base architecture and weights must match training. A different quantization can change behavior even when tensor names and dimensions load correctly.
- Keep the adapter-backed model under an experimental tag until critical prompts have been compared with the fused reference.

Ollama's current direct Safetensors importer does not list Qwen adapters. An MLX-LM directory containing `adapters.safetensors` and MLX's training `adapter_config.json` is not directly importable; Ollama reports that no Modelfile or Safetensors files were found. Convert it to GGUF first.

## MLX-LM to GGUF

MLX stores each linear adapter as:

- `lora_a`: `[input, rank]`
- `lora_b`: `[rank, output]`
- effective delta: `scale * lora_b.T @ lora_a.T`

To make a temporary Hugging Face PEFT adapter:

1. Rename tensors to `base_model.model.<module>.lora_A.weight` and `.lora_B.weight`.
2. Transpose both matrices. PEFT expects A as `[rank, input]` and B as `[output, rank]`.
3. Set PEFT rank to the MLX rank and `lora_alpha = MLX scale * rank`, preserving the effective multiplier because PEFT/GGUF applies `alpha / rank`.
4. Convert the PEFT directory with llama.cpp's `convert_lora_to_gguf.py`, passing the exact base model config. F16 is compact enough for typical rank-8 adapters and avoids another lossy adapter quantization.

For Herd's Qwen2.5 7B round three, 224 MLX tensors / 44 MB became a valid 23 MB F16 GGUF adapter. Ollama recognized it as a Qwen2 adapter.

## Seed the shared base inside Runpod

Avoid uploading the base from the workstation. On a load-balancing endpoint whose `OLLAMA_MODELS` points at the mounted network volume, call Ollama's native API:

```sh
curl https://ENDPOINT_ID.api.runpod.ai/api/tags \
  -H "Authorization: Bearer $RUNPOD_API_KEY"

curl --no-buffer https://ENDPOINT_ID.api.runpod.ai/api/pull \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"qwen2.5:7b-instruct","stream":true}'
```

This was verified against the `bardtown-npc-q3` load-balancing endpoint on 2026-08-22: `/api/tags` returned the volume-backed Ollama inventory after a cold start. Streaming the pull avoids an idle proxy timeout while Runpod downloads the base directly into the mounted volume.

### Current Herd serving path

Endpoint `k4ji23eemf5o2j` serves `herd-qwen25-7b:v3-test` from network volume
`7tfxebm4j6`. Public Herd clients do not call Runpod directly: they call
`https://llm.example.net/v1/model`, a CORS-restricted route on
`bardtown-llm-api` at Pinecone loopback port 3006. The game contains an
intentionally public, rate-limited gateway caller key; the service holds the
separate Runpod bearer token and pins the upstream URL and model.

During the 2026-08-22 stabilization pass the endpoint was deliberately set to
`workersMin: 1`, `workersMax: 1`, and `idleTimeout: 300` after one resumed worker
failed to become ready. A subsequent pinned worker answered `/api/tags` in 0.8s
and a full gateway chat in 3.6s. The observed worker rate was $0.74/hour. Do not
restore `workersMin: 0` until the user explicitly ends the stabilization window;
read actual spend with `runpodctl billing serverless`.

## Upload only the new layers

Create the adapter-backed model locally after the base exists locally. Its Ollama manifest will reference the base model layer plus small adapter, system, parameter, template, license, and config blobs.

Before sync, compare every referenced digest with `s3://<volume>/models/blobs/`. Upload only missing small blobs and the new manifest. Do not use a selective sync implementation that blindly includes every manifest digest: it will re-upload the multi-gigabyte base even when Runpod already pulled it.

After upload, verify `/api/tags`, then send deterministic identity, safety, and domain prompts through the remote model. Compare them with the fused local reference. If a stock Ollama quantization weakens a critical behavior, either keep the adapter tag experimental or seed an exact compatible base; adapter-only convenience is not evidence of behavioral equivalence.

## Cost and cleanup

Cloud-side pulls and tests wake a worker. Check cost with `runpodctl billing serverless`, and inspect worker state before walking away. Preserve the volume, but do not assume `workersMin: 0` guarantees an already-warm worker has stopped.
