# MPS feature guards & dependency landmines

## Arg-level guards — `finetrainers/args.py::_validate_device_args`

Runs inside `_validate_args` during `BaseArgs.parse_args()`; fires only when
`get_device_info()` resolves to `mps`. All fail loudly with an actionable message:

| Request                                         | Guard reason                                         | Steer to                          |
| ----------------------------------------------- | ---------------------------------------------------- | --------------------------------- |
| any `--*_degree > 1`                            | single unified-memory device; NCCL/DTensor are CUDA  | all degrees 1, accelerate backend |
| `--layerwise_upcasting_modules`                 | float8 dtypes unsupported on MPS                     | bf16                              |
| `--optimizer *bnb*`                             | bitsandbytes is CUDA-only                            | `adamw` / `adam`                  |
| attention provider ∉ {`native`, `_native_math`} | flash/sage/xformers/cudnn/efficient are CUDA kernels | `native` (SDPA)                   |

Caveat: tests that set `BaseArgs` fields programmatically (like `tests/trainer/*`) bypass
argparse and therefore these guards.

The attention default is already `native` (`FINETRAINERS_ATTN_PROVIDER` env, defaults
`"native"` in `constants.py`) — the happy path needs no flags.

## Env vars

- `PYTORCH_ENABLE_MPS_FALLBACK=1` — ops without MPS kernels fall back to CPU instead of
  raising. Set in `train_mps.sh`; `trainer/base.py` warns if unset. Each fallback is a
  hidden CPU round-trip — a later perf pass should census them.
- `FINETRAINERS_DEVICE` — force device (see single-device-lane.md).
- `WANDB_MODE=offline` in the recipe.

## Dependency landmines on macOS arm64 (as of 2026-07)

- **decord: no arm64 wheels, period** (eva-decord ships manylinux/win only). Fixed in
  `finetrainers/data/dataset.py`: `import decord` is `try/except → None`, and video-sample
  detection uses a `_VIDEO_READER_TYPES` tuple built from whatever imports.
- **Video decode is `datasets`-version-dispatched** in `dataset.py::_preprocess_video`:
  `<3.4.0` decord · `<4.0.0` torchvision VideoReader (dead on torchvision ≥0.25, API
  removed) · `>=4.0.0` **torchcodec** `VideoDecoder.get_all_frames().data` (NCHW already,
  no permute). On a Mac: `datasets>=4` + `pip install torchcodec av`.
- **torch ≥2.11 removed `_AttentionOp` / `_templated_ring_attention_backward`** from
  `torch.distributed.tensor.experimental._attention`; `models/attention_dispatch.py`
  imports them per-symbol with fallbacks (they're only used by context-parallel ring
  attention — unreachable on MPS).
- **bitsandbytes**: don't install; the default `adamw` path never imports it.
- **Python**: use the repo's `.venv` (3.12, created with uv). The pyenv-global 3.14 is
  missing wheels for half the stack. `make quality` = `.venv/bin/ruff format --check` +
  `.venv/bin/ruff check` (bare `ruff` isn't on PATH).

## Tested-good stack (recorded in docs/apple_silicon.md)

torch 2.12.1 · torchvision 0.27.1 · datasets 5.0.0 · torchcodec 0.14.0 · diffusers 0.39.0
· accelerate 1.13.0 · peft 0.19.1 · Python 3.12.
