---
topic_id: "v2:LEIJ"
topic_path: "metal-renderer/metal-core"
semantic_id: "3e2kgHEqUK9LnTNYQnpjZgpoWoMUMAAM"
related_ids:
  - "v_-mL386UidNhTNMcngz7JppGoKEsAAB"
  - "znmiBn-4GmUp3TuYdxgSddlYU6Mc8AAJ"
---
# Metal / MSL renderer references — local notes

Source-cited working notes for this project's **hand-rolled Metal renderer** (the native iOS
twin of the web stereo path): `ios/KaraokeVR/StereoARRenderer.swift` + `Passthrough.metal`,
drawing the passthrough + depth effects twice per frame on a phone GPU. Each file cites its
origin at the top (Apple/MSL doc URL or a `file:line` in this repo) and is grounded — no notes
from memory. These are written and consulted by the `metal-renderer` and `metal-fx-researcher`
agents; reuse before re-deriving, and keep additions lean and source-cited.

## Index

- **fragment-effect-fusion-and-cost.md** — fragment-effect fusion safety + the per-eye tap/cost
  budget for this stereo renderer.
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
- **procedural-prop-materials.md** — procedural prop material patterns for the hand-rolled renderer.
- **additive-translucent-prop-geometry.md** — additive self-illuminated translucent geometry
  (beam shafts, glow volumes) without shading/occluding the scene. (Merged from the
  karaoke-headset project-local shelf 2026-07.)
- **vision-overlay-passthrough-mapping.md** — aligning 2D Vision-point overlays to the
  passthrough quad's image→screen mapping. (Merged from the project-local shelf 2026-07.)

Cross-shelf: this is the RENDERING-Metal shelf; compute Metal (MSL kernels, MPS, dispatch) is
[[apple-silicon:README]], and [[gpu-rosetta]] (repo root) disambiguates all the GPU shelves.
