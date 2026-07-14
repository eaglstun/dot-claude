# The single-device MPS lane

How a plain `python train.py --parallel_backend accelerate` run resolves to MPS. Line
numbers drift — re-grep symbols before editing.

## Device resolution — one chokepoint

`finetrainers/utils/torch.py::get_device_info()`:

1. `FINETRAINERS_DEVICE` env var (`mps`/`cuda`/`cpu`) wins if set — validated, raises on junk.
2. Otherwise torch's `_get_available_device_type()` (returns `"mps"` on Apple Silicon).
3. Otherwise MPS → CUDA → CPU availability order (the old code fell back to `"cuda"` and
   crashed on Macs).

`FINETRAINERS_DEVICE=cpu` is the way to run a CPU comparison on the same machine — note it
also **skips the MPS arg guards** (you're not on mps anymore).

Note: `parallel/accelerate.py` and `parallel/ptd.py` capture `get_device_info()` at module
import — set the env var before importing finetrainers.

## world_size and comm backend

`trainer/base.py::_init_distributed`:

- `world_size` defaults to `torch.cuda.device_count()` **only on CUDA**; `1` otherwise
  (used to be 0 on Macs → instant death).
- comm backend via `_default_comm_backend(device_type)`: `nccl` on cuda, `gloo` otherwise.
- Warns at startup if on MPS and `PYTORCH_ENABLE_MPS_FALLBACK` ≠ `1`.

## The Accelerate ws=1 trap (the subtle one)

`parallel/accelerate.py::AccelerateParallelBackend.__init__`, ws==1 branch: it only passes
`InitProcessGroupKwargs(backend=...)` to `Accelerator` **when `LOCAL_RANK` is set** (i.e.
under a real launcher). Why: accelerate's `PartialState` treats an explicit backend as "we
are distributed"; with no launcher env vars it never calls `init_process_group`, then dies
in `torch.distributed.get_world_size()`. With no backend passed, PartialState lands in
`DistributedType.NO` and picks `mps` as the device. This is why the Mac lane is plain
`python train.py`.

Corollary: `accelerate launch --num_processes 1` on a Mac sets `LOCAL_RANK` → gloo →
`DistributedType.MULTI_CPU` → **device becomes cpu silently**. Don't use the launcher.

## What never runs at ws=1

Every `get_mesh()` call site in `sft_trainer`/`control_trainer` is gated behind a
parallelism flag (cp/tp/fsdp/ddp/pp/dp>1) that is false at ws=1 — the empty-mesh
`init_device_mesh` in `accelerate.py::get_mesh` is unreachable on this lane. Same for
`apply_fsdp2`/`apply_ddp`; the trainer falls through to `parallel_backend.prepare_model()`.

`parallel/ptd.py` guards `_device_module.set_device(...)` with `hasattr` (torch.mps has no
`set_device`), so constructing the PTD backend doesn't crash — but PTD is not the Mac lane.

## MPS-safe utilities

- `utils/memory.py::get_memory_statistics` — MPS branch fills `memory_allocated` +
  `memory_reserved` (driver), leaves max-stats `None` (no MPS API); the dict builder is
  None-safe (used to `round(None)` → crash mid-train-loop).
- `utils/memory.py::free_memory` — `torch.mps.empty_cache()` branch.
- `utils/memory.py::reset_peak_memory_stats(device)` — no-op on MPS; the trainers call
  this instead of bare `torch.cuda.reset_peak_memory_stats` (4 call sites swapped).
- `utils/torch.py::synchronize_device` — already had an MPS branch pre-port.
- **Gradient clipping**: both trainers pass `foreach=True if device is cuda else None` to
  `_clip_grad_norm_while_handling_failing_dtensor_cases` — the foreach API is
  CUDA/CPU-only; hardcoded `True` silently skipped clipping on MPS (warning only) and
  dropped `train/grad_norm` from logs.
- **Checkpoint resume**: `AccelerateCheckpointer.load_model_hook` uses
  `torch.load(..., weights_only=False)` — states.pt holds a `TrainState` dataclass that
  the torch≥2.6 `weights_only=True` default refuses to unpickle. The file is
  self-written, so trusted-load is correct.
