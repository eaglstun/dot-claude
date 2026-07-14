# CPU ↔ MPS parity testing

The discipline (from the CT2 port, `ct2-internals` op-parity methodology): MPS failures
are **silent wrong numbers, not crashes** — "training ran" proves nothing. CPU is the
oracle; run the identical seeded computation on both devices and compare within a
documented per-dtype tolerance.

## The gate test

`tests/mps/test_cpu_mps_parity.py` — LTX-Video transformer forward (the tiny
`DummyLTXVideoModelSpecification` from `tests/models/ltx_video/base_specification.py`,
seeded weights + seeded inputs), CPU vs MPS:

```bash
.venv/bin/python -m pytest -s tests/mps/test_cpu_mps_parity.py
```

Tolerances (documented in the test docstring):

- **fp32: atol/rtol 1e-4** — only GEMM accumulation-order reassociation differs.
- **bf16: atol/rtol 5e-2** — ~2–3 significant decimal digits, per-kernel accumulation
  differences compound across layers.

Skips via `pytest.mark.skipif(not torch.backends.mps.is_available())` — CI-safe on Linux.
Also asserts both outputs are finite (the fp16/bf16 "confident garbage" check).

## E2E training on MPS (dummy models, real loop)

The existing accelerate dp=1 SFT tests run on MPS under **plain pytest** (no launcher —
that's the point of the ws=1 lane):

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -m pytest -q \
  "tests/trainer/test_sft_trainer.py::SFTTrainerLTXVideoLoRATests___Accelerate::test___dp_degree_1___batch_size_1_0"  # and _1 (precomputation)
```

Both pass (2026-07): 10 steps, dataset decode → text-encoder → VAE → transformer
fwd/bwd → optimizer → checkpoint, all on mps.

## Extending to a new model

1. Reuse that model's dummy spec under `tests/models/<model>/`.
2. Add a forward-parity case mirroring the LTX one (seeded inputs shaped to the dummy
   config; check the dummy spec for channel/caption dims).
3. Keep per-dtype tolerances documented in the docstring; if bf16 needs looser than 5e-2,
   that's a smell — bisect layers before widening.
4. Manual acceptance beyond the gate: run the model's `train_mps.sh`-style recipe, expect
   finite decreasing loss and a checkpoint that reloads.
