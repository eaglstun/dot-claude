# PyTorch MPS backend on Mac

Primary Apple source: [Accelerated PyTorch training on Mac](https://developer.apple.com/metal/pytorch/)
(checked 2026-09-01).

Supporting first-party PyTorch sources:

- [MPS backend note](https://docs.pytorch.org/docs/stable/notes/mps.html)
- [MPS package reference](https://docs.pytorch.org/docs/stable/mps.html)
- [MPS environment variables](https://docs.pytorch.org/docs/stable/mps_environment_variables.html)
- [MPS backend contributor and profiler wiki](https://github.com/pytorch/pytorch/wiki/MPS-Backend)
- [PyTorch installation selector](https://pytorch.org/get-started/locally/)

## Architecture

PyTorch exposes the Apple GPU as the `mps` device. Apple describes that backend as a mixture of
MPSGraph graph/primitives, tuned MPS kernels, and custom Metal kernels. Do not collapse "MPS backend"
into "MPSGraph only" or "custom Metal only": inspect the operator and choose the implementation path
that fits the missing capability and performance requirement.

For a new MPS operator, Apple's linked contributor guidance gives this order:

1. Bridge to an existing MPS operation when one implements the PyTorch semantics.
2. Use a custom Metal kernel for a performance-critical operation without a suitable MPS primitive.
3. Use CPU fallback only as a last resort for a non-performance-critical operation.

This is triage guidance, not a substitute for current repository conventions. Existing ATen code,
tests, maintainers' direction, and an explicitly requested MPSGraph-to-Metal migration determine the
actual implementation.

## Consumer setup snapshot

On 2026-09-01, Apple's page labeled PyTorch 2.11.0 as its latest stable release and listed these
requirements for that release:

- a Mac with Apple silicon;
- macOS 14.0 or later;
- Python 3.10 or later;
- Xcode command-line tools, installed with `xcode-select --install`.

The page's stable consumer command was:

```bash
pip3 install torch torchvision torchaudio
```

Its nightly command for the newest MPS support was:

```bash
pip3 install --pre torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/nightly/cpu
```

These are binary-install instructions for users. They do not override a checkout's source-build
recipe. Release numbers, OS floors, Python ranges, and install commands change independently and may
lag between Apple and PyTorch pages, so re-open both the Apple page and PyTorch's installation selector
before giving current setup advice.

## Availability check

Apple verifies MPS by checking `torch.backends.mps.is_available()`, creating a tensor on
`torch.device("mps")`, and expecting its printed device to be `mps:0`:

```python
import torch

if torch.backends.mps.is_available():
    device = torch.device("mps")
    print(torch.ones(1, device=device))
else:
    print("MPS device not found.")
```

For diagnosis, also distinguish build support from runtime availability:

- `torch.backends.mps.is_built()` says whether the installed PyTorch binary was built with MPS.
- `torch.backends.mps.is_available()` additionally requires a supported macOS runtime and device.

Do not infer why MPS is unavailable from `is_available()` alone.

## Profiling and support

Apple's page links the PyTorch MPS wiki for both operator contribution guidance and profiling. The
wiki describes PyTorch's MPS profiler in terms of OS Signposts and Instruments. Treat wiki signatures
as historical guidance: check the current `torch.mps.profiler` API and the checkout before writing a
profiling command.

Apple labels the MPS backend beta and directs bug reports to the PyTorch issue tracker with the
`module: mps` label. Repository AI/contribution policy still governs any issue or pull-request action;
reading this reference never authorizes an agent to create or modify GitHub content.

## Freshness rule

The Apple page is a useful product-level map, but it contains release-specific values and links to a
PyTorch wiki last edited in 2024. Re-open live sources for setup/support questions, and use the current
checkout as the authority for implementation details.

### Worked example: PyTorch MPS backend

In a PyTorch checkout, `torch/backends/mps/__init__.py` owns the public build and
availability checks. MPSGraph host implementations live under `aten/src/ATen/native/mps/operations/`;
custom shaders live under `aten/src/ATen/native/mps/kernels/` and are dispatched through the bundled
`MetalShaderLibrary`. The checkout's `AGENTS.md` owns its source-build and test commands, so the
consumer installation commands above never replace that local recipe.
