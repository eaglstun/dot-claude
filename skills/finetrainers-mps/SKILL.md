---
name: finetrainers-mps
version: 1.0.0
public: true
description: >-
  Apple Silicon (MPS) lane of the user's finetrainers fork. Use when training or debugging
  finetrainers on a Mac, touching the MPS guards or single-device Accelerate path,
  running/extending the CPU↔MPS parity tests, or hitting device/decode errors on macOS
  (decord, torchcodec, NCCL, LOCAL_RANK).
semantic_id: "05UspR0OZdgI8hlW791HnwDmz88XoAAI"
related_ids:
  - "wWUprU8jbbAA66pVl10GtCVUFl6LIAAD"
  - "0Y8a9xsxPYwgsuPVz_hFNSxmNEx7AAAN"
topic_id: "v2:NGNK"
topic_path: "apple-accelerate/mps-inference"
---

# finetrainers on Apple Silicon (MPS)

The port (executed 2026-07-08 per `docs/apple_silicon/PORT_PLAN.md` in the repo) carves a
**single-process, world_size=1, Accelerate-backend** lane out of a distributed-CUDA-first
codebase. Correctness first; no Metal kernels — everything rides `torch.mps`.
User-facing doc: `docs/apple_silicon.md` in the repo. Launch recipe:
`examples/training/sft/ltx_video/crush_smol_lora/train_mps.sh`.

**The one rule:** on a Mac, launch with **plain `python train.py`** — no `torchrun`, no
`accelerate launch` (the launcher's env vars route Accelerate into MULTI_CPU/gloo and the
device silently becomes CPU).

## References

- **[references/single-device-lane.md](references/single-device-lane.md)** — how device
  resolution, world_size, comm backend, and the Accelerate ws=1 path work; the
  `LOCAL_RANK`/`InitProcessGroupKwargs` trap; `FINETRAINERS_DEVICE` escape hatch.
- **[references/feature-guards.md](references/feature-guards.md)** — what's blocked on MPS
  and where each guard lives (`args.py::_validate_device_args`); env vars; dependency
  landmines (decord→torchcodec, bitsandbytes, torch 2.11 CP-symbol removals).
- **[references/parity-testing.md](references/parity-testing.md)** — the CPU-as-oracle
  discipline (from `ct2-internals`), tolerances, how to run and extend
  `tests/mps/test_cpu_mps_parity.py`, and the E2E dummy-model tests that run on MPS.

## Cross-links

- `apple-silicon` skill — Metal/MSL ground truth (only relevant if a future phase
  hand-writes kernels; not this lane).
- `ct2-internals` skill — the op-parity test methodology this port's tests follow.
- Memory `finetrainers-apple-silicon-port` — project status and discovery log.
