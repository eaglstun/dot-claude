---
topic_id: "v2:KAEL"
topic_path: "cuda-gpu"
semantic_id: "DnvnaKG83eW1tLd7GVw6emSYqTIK8AAN"
related_ids:
  - "JhpzepiG1OMVCfVaGXN5KPcU6RDj8AAA"
  - "xfMyKG4UYqd1lnJjWlk5ZuGwIr6IcAAC"
---
# GPU Rosetta — CUDA ↔ Metal concept map + crosslink conventions

The hub for the GPU-adjacent shelves. Two jobs: (1) say which shelf owns which
kind of GPU knowledge, (2) map equivalent concepts across vendors so a reader
on one side can find the other side's file without guessing terminology.

## Which shelf owns what (the three Metals problem)

| Shelf                                              | Flavor                                                                                                                             | Written by                                      |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| [[apple-silicon:README]]                           | **Compute Metal** — MSL kernels, MPS, GEMM, dispatch, for the CTranslate2 Metal backend                                            | `apple-silicon` skill                           |
| [[metal:README]]                                   | **Rendering Metal** — stereo passes, depth effects, encoders/textures, for the karaoke-headset renderer                            | `metal-renderer` / `metal-fx-researcher` agents |
| [[cuda:README]]                                    | **NVIDIA CUDA** — the CT2 reference GPU backend the Metal backend mirrors                                                          | `cuda-references` agent                         |
| `~/.claude/skills/ffglitch/references/gpu-post.md` | **Video-pipeline Metal** — glitchgpu compute CLI, VideoToolbox, Resolve DCTL (skill-local; links out to shelves, nothing links in) | ffglitch skill                                  |
| [[threejs:README]]                                 | Web graphics (pinned r132, phone GPU)                                                                                              | `threejs-researcher` agent                      |
| [[ct2-internals:README]]                           | Device-agnostic engine structure above any backend                                                                                 | `ct2-internals` skill                           |

Rule of thumb: "how do I make the GPU compute X" → apple-silicon/cuda;
"how do I draw X" → metal; "how does CT2 wire X" → ct2-internals.

## Terminology map

| Concept                                | CUDA says                    | Metal says                                 |
| -------------------------------------- | ---------------------------- | ------------------------------------------ |
| SIMD execution group (32 wide on both) | warp                         | simdgroup                                  |
| Cooperating thread block               | block / CTA                  | threadgroup                                |
| Whole launch                           | grid                         | grid                                       |
| Fast on-chip scratch                   | shared memory                | threadgroup memory                         |
| Block-level barrier                    | `__syncthreads()`            | `threadgroup_barrier()`                    |
| Lane exchange                          | `__shfl_sync()`              | `simd_shuffle()`                           |
| Work submission                        | stream                       | command queue / command buffer             |
| Cross-stream sync                      | event                        | MTLEvent / MTLSharedEvent / MTLFence       |
| Matrix hardware                        | Tensor Cores                 | simdgroup_matrix (+ Metal 4 tensors)       |
| Feature gating                         | compute capability (`sm_XX`) | MTLGPUFamily                               |
| Launch config                          | `<<<grid, block>>>`          | `dispatchThreadgroups` / `dispatchThreads` |

## Concept crosslinks (file ↔ file)

- **SIMD-group ops & atomics** — [[cuda:warp-primitives-atomics]] ↔
  [[apple-silicon:simd-group-functions]] + [[apple-silicon:atomic-functions]].
  Gotcha: CUDA (Volta+) has independent thread scheduling and `_sync` masks;
  Metal simdgroups execute in lockstep with no mask concept.
- **Scratch memory & occupancy** — [[cuda:memory-model-kernels]] ↔
  [[apple-silicon:msl-address-spaces]] +
  [[apple-silicon:occupancy-and-threadgroup-memory]]. Gotcha: Apple caps
  threadgroup memory at 32 KB; CUDA shared memory is configurable up to
  ~100–228 KB depending on architecture.
- **GEMM** — [[cuda:cublas-gemm]] ↔ [[apple-silicon:mps-matrix-multiplication]]
  - [[apple-silicon:gemm-layouts-and-transpose-conventions]]. Gotcha: cuBLAS is
    column-major by convention; MPS matrices are row-major descriptors.
- **Streams / queues & events** — [[cuda:runtime-streams-events]] ↔
  [[apple-silicon:concurrent-dispatch-and-encoder-semantics]] +
  [[apple-silicon:mtlevent-and-mtlfence]]. Gotcha: a CUDA stream is closest to
  a serial command queue, but Metal work is batched into explicit command
  buffers you commit; there's no implicit "current stream".
- **Matrix hardware & feature gating** — [[cuda:compute-capability-tensor-cores]]
  ↔ [[apple-silicon:simdgroup-matrix-functions]] +
  [[apple-silicon:mtlgpufamily-and-feature-availability]] +
  [[apple-silicon:metal4-tensors-and-mpp]].
- **Kernel launch & dispatch** — [[cuda:memory-model-kernels]] ↔
  [[apple-silicon:compute-kernels-and-dispatch]]. Gotcha: Metal's
  `dispatchThreads` supports non-uniform threadgroups (no manual bounds check);
  CUDA kernels always bounds-check the tail block.
- **Device memory & residency** — [[cuda:memory-model-kernels]] ↔
  [[apple-silicon:resource-storage-modes-and-options]] +
  [[apple-silicon:memory-footprint-and-residency]]. Gotcha: unified memory is
  the default reality on Apple silicon (`.shared`, no copies); on discrete
  NVIDIA it's an opt-in abstraction with page-migration cost.
- **Algorithm libraries** — [[cuda:thrust]] has no single Metal twin; nearest
  neighbors are the MPS families ([[apple-silicon:mps-softmax-and-topk]],
  [[apple-silicon:mps-matrix-vector-multiplication]]) plus hand-rolled kernels.

## Crosslink conventions (all shelves)

- **Syntax:** `[[shelf:file]]` resolves to `~/.claude/references/<shelf>/<file>.md`.
  Bare `[[file]]` = same shelf, falling back to the repo root (hub files like
  this one — link it as `[[gpu-rosetta]]`).
- **MSL collision:** Metal attribute syntax IS double brackets
  (`[[thread_position_in_grid]]`), so all MSL attributes in prose must sit in
  code spans/fences — the auditor ignores code and treats everything else as a
  link.
- **Placement:** a `### See also` footer section; inline only when load-bearing.
- **Every link carries a claim** — "CUDA twin of", "contradicts", "superset" —
  never a bare pointer. A claim can be judged stale on read; a bare link can't.
- **Direction:** global shelves may link to each other and to this rosetta.
  Skill-local and project-local reference files may link OUT to shelves but
  nothing links INTO them (shelves never depend on a project existing).
- **Don't force bidirectionality** at write time; `audit-crosslinks.sh` (repo
  root) reports dangling links and asymmetric pairs for periodic cleanup.
- **Namespace boundary:** bare `[[name]]` outside this repo is someone else's
  convention (the user's memory wikilinks use the same syntax) — the auditor only
  judges namespaced links in external dirs, bare ones only inside this repo.
- **Writers:** before adding a new GPU-topic file, grep this rosetta and the
  shelf READMEs for the concept; add See-also links both to and (cheaply) from
  the twins you touch.
