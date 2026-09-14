---
name: scenekit
description: SceneKit reference for materials, shader modifiers, lighting, shadows, cameras, projection, geometry, and asset formats on Apple platforms. Use when writing or debugging SceneKit, especially silent shader, transparency, shadow, or import failures.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: AWxCb312fZdpxRM94NnG6CI2WH2qcAAC
  related_ids: '["JGziC21y2zWJnQoM4nCH3JF4G4umcAAM","LeUiP2Wxs1sZbY0L8FmH2OF6WsGPEAAJ"]'
---

# SceneKit reference

Grounded in the iOS SDK headers (verified against **iOS 26.5**) and in behaviour
confirmed by experiment on simulator/device. Where something was established by
testing rather than documentation, it says so.

**SceneKit's status:** fully present and _not_ deprecated in the iOS 26.5 SDK —
the only `API_DEPRECATED` symbols in the framework are individual properties
retired back in iOS 11. Apple's momentum is behind RealityKit, so treat it as a
renderer with a finite but not imminent lifespan, and keep game logic out of it.

## References

| File                                   | Covers                                                                                     |
| -------------------------------------- | ------------------------------------------------------------------------------------------ |
| `references/shader-modifiers.md`       | Entry points, the complete uniform list, the uniform-reset trap, merging modifiers         |
| `references/materials-transparency.md` | Lighting models, PBR vs Blinn, Fresnel and reflections, transparency rules, multi-material |
| `references/lighting-and-shadows.md`   | Shadow modes, radius/sample-count pairing, why shadows render nothing, lighting categories |
| `references/cameras-and-projection.md` | Orthographic and isometric setup, `orthographicScale` semantics, what ortho takes away     |
| `references/assets-and-formats.md`     | No glTF support, the USDZ route, Blender export traps, bundling                            |

## The five that waste the most time

1. **Assigning `material.shaderModifiers` drops uniform values previously set by
   KVC.** Set them again afterwards, or push them every frame. Fails silently —
   the shader runs with zeros.
2. **SceneKit cannot load glTF/GLB at all** — the output format of essentially
   every 3D-generation service. Convert to USDZ.
3. **Transparent materials need `writesToDepthBuffer = false` and a raised
   `renderingOrder`**, or they occlude whatever is behind them.
4. **A shadow that renders nothing is usually the light's _direction_,** not its
   settings. If the light and camera are on the same side, every shadow falls
   behind its own caster and is invisible.
5. **Under orthographic projection an infinite ground plane fills the entire
   screen.** All rays are parallel, so there is no horizon anywhere.
