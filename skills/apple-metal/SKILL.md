---
name: apple-metal
description: Real-time Metal rendering reference for games and AR apps. Use for stereo rendering, depth and temporal effects, render passes, mesh/material paths, picking, or multi-draw encoder traps. Use apple-silicon for general Metal APIs and GPU compute.
metadata:
  topic_id: v2:LEIJ
  topic_path: metal-renderer/metal-core
  semantic_id: 3e2kgHEqUK9LnTNYQnpjZgpoWoMUMAAM
  related_ids: '["v_-mL386UidNhTNMcngz7JppGoKEsAAB","BODE5nU53h-bmQtYcEqiUtlY-qO2AAAC"]'
---

# Metal / MSL renderer references

Source-cited working notes for **hand-rolled Metal renderers** — real-time rendering technique,
not API reference. Each file cites its origin at the top (an Apple/MSL doc URL, an external
technique reference, or an attributed provenance line saying what the finding was measured or
diagnosed on) and is grounded — no notes from memory.

Several of these were learned building a stereo AR passthrough renderer on a phone-class GPU,
which is why per-eye cost budgets and stereo-fusion safety recur. **The techniques are general**;
where a number was measured on specific hardware, the file says so — re-measure elsewhere.

**Boundary:** this shelf is _rendering_. The general Metal API surface and GPU-compute material —
`MTLBuffer`, heaps, argument buffers, pipeline compilation, GPU families and feature gating,
frame capture and validation, command-buffer errors, ray tracing — lives in **`apple-silicon`**.

## Index

- **tbdr-tile-memory-and-imageblocks.md** — how Apple's tile-based deferred renderer actually
  works: free hidden-surface removal, tile memory, imageblocks, tile shaders, raster order
  groups, and A11+ MSAA sample-coverage control. _Read first if you're deciding where a pass
  should live._
- **fragment-effect-fusion-and-cost.md** — fragment-effect fusion safety + the per-eye tap/cost
  budget for stereo / draw-twice renderers.
- **per-eye-temporal-accumulation.md** — trails / persistence via per-eye accumulation without
  breaking stereo fusion.
- **depth-stylization.md** — edge / normal / stylization recipes for the depth-passthrough pass.
- **depth-prepass-occludes-virtual-content.md** — real-world depth prepass occluding virtual
  content, consistent across all modes.
- **distant-backdrop-occlusion.md** — distant backdrop occlusion + follow-me ("mesa") anchoring.
- **encoder-texture-slot-clobber.md** — shared-encoder texture-slot clobber across the per-eye
  loop (the "only the right eye is wrong" tell).
- **gaze-dwell-picker.md** — gaze raycast + dwell select (head-pose → hit-test → ring).
- **static-glb-mesh.md** — static GLB mesh → Metal (no rig).
- **skinned-mesh-runtime.md** — skinned (rigged + animated) GLB runtime, native Metal LBS.
- **effects-backlog.md** — renderer effects backlog (depth / outline / trails).
- **procedural-prop-materials.md** — procedural prop materials without UVs (shaded surfaces from vertex normals alone).
- **additive-translucent-prop-geometry.md** — additive self-illuminated translucent geometry
  (beam shafts, glow volumes) without shading/occluding the scene.
- **vision-overlay-passthrough-mapping.md** — aligning 2D Vision-point overlays to the
  passthrough quad's image→screen mapping.

Cross-shelf: this is the RENDERING-Metal shelf; compute Metal (MSL kernels, MPS, dispatch) is
[[apple-silicon:README]], and [[gpu-rosetta]] (repo root) disambiguates all the GPU shelves.
