---
topic_id: "v2:KBMK"
topic_path: "cuda-gpu"
semantic_id: "nTS_Z6Hu0Sa33FYn7FiyWtzDydK4gAAF"
related_ids:
  - "SQyzozHPOGal8Nf7LUgaGgIvxLmwAAAH"
  - "UPKrpWJ7wPav9FO37Um-04ArBvcQIAAL"
---
# Install / version-compat + diagnostics

- Source: https://github.com/facebookresearch/xformers/blob/v0.0.35/README.md (install + troubleshooting)
  - https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/info.py
  - https://github.com/facebookresearch/xformers/blob/main/CHANGELOG.md
- Fetched: 2026-06-29
- Reflects: **xFormers 0.0.35** (latest released, 2026-02-20). **0.0.36 is unreleased** on `main`.

## The #1 rule

xFormers ships **prebuilt wheels pinned to a specific torch + CUDA build**. A mismatch either fails to
import (`xFormersInvalidLibException`) or silently disables the C++/CUDA kernels so attention falls
back to a slow path. **Match the wheel to your installed torch+CUDA before debugging model code.**

## Version matrix (this release)

- xFormers **0.0.35** requires **PyTorch 2.10.0**. (0.0.34 migrated to PyTorch's stable API/ABI for
  2.10+ compat; 0.0.35 adds free-threading Python support and PyTorch 2.10.0+ wheels.)
- Each xFormers release pins one torch minor. Upgrading torch generally requires upgrading xFormers
  (and vice-versa). Check the CHANGELOG/README for the exact pairing of the version you install.

## Install (Linux & Windows, recommended — stable wheels)

```bash
# pick the CUDA build matching your torch install:
pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu126   # CUDA 12.6
pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu128   # CUDA 12.8
pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu130   # CUDA 13.0
pip3 install -U xformers --index-url https://download.pytorch.org/whl/rocm7.1 # ROCm 7.1 (EXPERIMENTAL, linux)
```

Development binaries (matches stable requirements): `pip install --pre -U xformers`.

## Build from source (for a non-matching / nightly torch)

```bash
pip install ninja                       # makes the build much faster
# torch MUST already be installed first
pip install -v --no-build-isolation -U git+https://github.com/facebookresearch/xformers.git@main#egg=xformers
# can take dozens of minutes
```

Troubleshooting a source build:

- NVCC version must match the active CUDA runtime (`module load cuda/xx.x`), and GCC must match NVCC.
- Set `TORCH_CUDA_ARCH_LIST` to your target archs, e.g.
  `export TORCH_CUDA_ARCH_LIST="6.0;6.1;6.2;7.0;7.2;7.5;8.0;8.6"` (comprehensive but slow to build).
- If the build OOMs, lower ninja parallelism: `MAX_JOBS=2`.
- Windows "Filename longer than 260 characters": enable long paths + `git config --global core.longpaths true`.

## Diagnostics: `python -m xformers.info`

Runs `xformers/info.py::print_info()`. It iterates `OPERATORS_REGISTRY` and prints, per operator,
`available` / `unavailable` — i.e. **which memory-efficient / flash / triton kernels actually compiled
and loaded on this machine**. This is the fastest way to confirm "no kernel available / silently slow".

Fields it prints:

- `xFormers <version>` header.
- `<category>.<op-name>: available|unavailable` for every registered op (e.g.
  `memory_efficient_attention.cutlassF-pt`, `...flshattF@<ver>`, `memory_efficient_attention.triton_splitKF`).
- `is_triton_available`.
- `pytorch.version`, `pytorch.cuda` (available / not available).
- `gpu.compute_capability`, `gpu.name` (current CUDA device).
- `dcgm_profiler`.
- Build metadata (when the C++ lib loaded): `build.cuda_version`, `build.hip_version`,
  `build.python_version`, `build.torch_version`, `build.env.*`, `build.nvcc_version`.
- `source.privacy` (open source vs fairinternal).

How to read it:

- An op showing **`unavailable`** while you expect it = wheel/torch/CUDA mismatch or unmet hardware
  (e.g. flash needs SM ≥ 8.0 + fp16/bf16). `build.info: none` means the compiled extension didn't load
  at all — reinstall the wheel matching your torch+CUDA.
- Compare `build.torch_version` / `build.cuda_version` against `pytorch.version` and your CUDA runtime;
  if they differ, that's the bug.

## Quick sanity check in Python

```python
import xformers.ops as xops, torch
inp = xops.fmha.Inputs(query=q, key=k, value=v, attn_bias=bias, p=0.0)
print(xops.fmha.flash.FwOp.not_supported_reasons(inp))   # [] means flash will run
```
