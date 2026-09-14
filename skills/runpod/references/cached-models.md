# Runpod cached models

Read this reference when selecting, configuring, or loading Runpod's native cached-model feature. It is separate from a user-created network volume: both mount below `/runpod-volume/`, but cached weights are host-local and Runpod-managed.

Official sources, checked 2026-09-04:

- [Cached models](https://docs.runpod.io/serverless/endpoints/model-caching)
- [Use Hugging Face models](https://docs.runpod.io/serverless/development/huggingface-models#use-cached-models)
- [Cached-model tutorial](https://docs.runpod.io/tutorials/serverless/model-caching-text)

## Choose this path when

- The exact model repository is on Hugging Face. Public, gated, and private repositories are supported; gated/private repositories require a Hugging Face access token with access.
- Cold-start time or download cost matters. Runpod tries to schedule on a host that already has the model. If it must populate a host first, it delays worker startup and says download time is not billed as worker time.
- The container should carry application/runtime code rather than a large weight layer.

Do not choose it for a private model that is not on Hugging Face; bake that artifact into the image or put it on a network volume. Check Runpod Public Endpoints first for an already-hosted stock model.

## Endpoint configuration

In the Serverless console, create or edit an endpoint and set **Model** to the Hugging Face repository identifier, for example `Qwen/Qwen2.5-0.5B-Instruct`. A Hugging Face deployment configures caching automatically. Docker, GitHub, and Hub deployments can also select a model in endpoint configuration.

Official Runpod worker images, including vLLM images, usually use the **Model** field or `MODEL_NAME` automatically. Treat every other image as a custom worker until its entrypoint proves otherwise.

## Custom-worker mount layout

The cache root is:

```text
/runpod-volume/huggingface-cache/hub/
```

Repositories follow the Hugging Face cache layout:

```text
models--{org}--{name}/
  refs/main                    # commit hash for main, when present
  snapshots/{commit-hash}/    # repository files
```

Resolve the snapshot dynamically. Prefer the hash named by `refs/main`; if it is absent, inspect `snapshots/` and fail clearly if no snapshot exists. Do not hardcode an example commit hash.

For Transformers workers, set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, pass the resolved local snapshot path, and use `local_files_only=True`. This makes a missing cache fail visibly instead of silently downloading during worker startup.

## Ollama and GGUF workers

Runpod caches a Hugging Face repository snapshot; it does not create an Ollama manifest or populate Ollama's blob store. An Ollama-based custom image therefore needs startup logic that:

1. Resolves the cached snapshot directory.
2. Selects the intended GGUF and Modelfile explicitly.
3. Imports the model into Ollama or points the serving runtime directly at that GGUF.
4. Avoids network fallback, and fails if the required artifact is absent.

Do not assume `MODEL_NAME` alone makes an arbitrary Ollama image cache-aware. Verify cold-start logs and invoke the shipping endpoint before treating the integration as complete.

For a Hugging Face repository containing a Q8 GGUF plus cards or tokenizer files, cache suitability depends on the custom entrypoint finding that GGUF reliably. If the repository contains several quantization variants, Runpod currently downloads all of them; consider a repository containing only the shipping quantization when storage and population time matter.

## Current limitations

- One cached model per endpoint.
- If one Hugging Face repository contains multiple quantization versions, Runpod currently downloads all of them; the endpoint cannot select only one quantization at cache-population time.
- Workers on the same host can share the cached model, but scheduling onto a cached host is an optimization rather than a guarantee. A cache miss delays worker startup while Runpod downloads the repository.
- The cache uses the same top-level mount prefix as network volumes, but Runpod documents cached-model loading as significantly faster than loading the same model from a network volume.

## Verification

After deployment, verify behavior rather than only reading endpoint configuration:

- Worker logs show the resolved path under `/runpod-volume/huggingface-cache/hub/`.
- No Hugging Face or model-weight download happens inside billed worker startup.
- The intended revision and quantization are loaded.
- A real inference request succeeds through the shipping endpoint.
- Billing is still checked with `runpodctl billing serverless`; cache use does not change the skill's billing source of truth.
