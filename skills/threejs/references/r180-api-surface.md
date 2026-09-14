---
topic_path: "metal-renderer/threejs-api"
related_ids:
  - "B8vc70Ea8gHZ-AsBpTvikNFJIsM8QAAP"
  - "ZG0w579Q2TWZLYoC9HqDQJlYMcmzAAAF"
semantic_id: "QUuwsXVf_be82AMiVDnhErj_Is-9YAAD"
---

# r180 API Surface — the CAPRICCIO import set

> **Pinned to Three.js r180 (0.180.0).** Every claim below was verified by parsing
> `node_modules/three/build/three.module.js` + `three.core.js` in an r180 project,
> diffed against an r132 project. When the live docs and this doc disagree, trust this doc.

Scope: the 45 symbols CAPRICCIO actually imports, listed in `src/vendor-imports.json`. This is
the **r180 twin** of `r132-api-gotchas.md`, and its real job is the seam between the two projects
— code copied from the headset repo into CAPRICCIO, or back.

## Existence is a non-issue; behaviour isn't

**44 of the 45 exist in both r132 and r180.** The single exception is **`SRGBColorSpace`**, which
is r180-only (arrived r152) — r132 uses `sRGBEncoding` instead. That trap already has a full
write-up in `color-management-and-ibl.md`.

So almost everything ports _by name_. What breaks is behaviour, and the renderer is where it hurts.

## The renderer/colour axis — where porting actually dies

Verified by occurrence count in each build:

| property                           | r132              | r180                                            |
| ---------------------------------- | ----------------- | ----------------------------------------------- |
| `renderer.outputEncoding`          | **26 refs**       | **0 — gone**                                    |
| `renderer.outputColorSpace`        | 0 — doesn't exist | **20 refs**                                     |
| `renderer.physicallyCorrectLights` | present           | **0 — gone**                                    |
| `renderer.useLegacyLights`         | doesn't exist     | **0 — also gone** (added r155, removed by r165) |

`useLegacyLights` is the one that catches people twice: the migration guides tell you to swap
`physicallyCorrectLights` for it, but by r180 **both are gone** and physical falloff is simply
the default. Don't write either name in CAPRICCIO.

Note `WebGLRenderer`'s _method_ list is identical across the two versions — the entire breakage
here is in properties, which a method diff cannot see.

## Removed between r132 and r180 — these throw

- **`BufferAttribute`**: `copyColorsArray`, `copyVector2sArray`, `copyVector3sArray`,
  `copyVector4sArray`
- **`BufferGeometry.merge()`** — use `mergeGeometries` from
  `examples/jsm/utils/BufferGeometryUtils.js`. (Careful: r132 spells that helper
  `mergeBufferGeometries` — the two projects need different import names. See
  `r132-api-gotchas.md`.)
- **`Color`**: `convertGammaToLinear`, `convertLinearToGamma`, `copyGammaToLinear`,
  `copyLinearToGamma` — the whole manual-gamma family, obsoleted by colour management.
- **`WebGLRenderTarget.setTexture()`** — genuinely gone (0 occurrences anywhere in the r180 build).

## Looks removed, is only inherited — don't chase this one

A naive class-body diff reports `WebGLRenderTarget` losing `clone`, `copy`, `dispose`, and
`setSize`. **It didn't.** In r180 the declaration is:

```js
class WebGLRenderTarget extends RenderTarget { … }
```

and `RenderTarget` (new base class, not present in r132) owns `clone` / `copy` / `dispose` /
`setSize` / `_setTextureOptions`. All four still work on the instance. Only `setTexture` is
actually missing.

## New in r180 — will not exist if you backport to the headset repo

- **`.copy()` on geometries**: `BoxGeometry`, `CylinderGeometry`, `PlaneGeometry`,
  `SphereGeometry`, `TorusGeometry`, `TubeGeometry`
- **`BufferAttribute`**: `addUpdateRange`, `clearUpdateRanges` (the multi-range replacement for
  the old single `updateRange`), `getComponent`, `setComponent`
- **`BufferGeometry`**: `getIndirect`, `setIndirect` (indirect draw support)
- **`InstancedMesh`**: `computeBoundingBox`, `computeBoundingSphere`, `getMorphAt`, `setMorphAt`
- **`Object3D`**: `getObjectsByProperty`, `onBeforeShadow`, `onAfterShadow`
- **`Mesh`**: `getVertexPosition`
- **`Raycaster`**: `setFromXRController`
- **`PerspectiveCamera`**: `getViewBounds`, `getViewSize`
- **`Quaternion`**: `random`, `toJSON`
- **`Vector3`**: `setFromColor`, `setFromEuler`, `randomDirection` — **`Vector2`**: `angleTo`
- **`Color`**: `applyMatrix3`, `getRGB`, `setFromVector3`
- **`DepthTexture`**: `copy`, `toJSON`

## Identical method surface in both versions

Safe to move code either direction, as far as methods go:

`CatmullRomCurve3`, `ConeGeometry`, `DirectionalLight`, `ExtrudeGeometry`, `FogExp2`, `Group`,
`HemisphereLight`, `Line`, `LineBasicMaterial`, `LineDashedMaterial`, `Matrix4`,
`MeshBasicMaterial`, `MeshLambertMaterial`, `MeshPhongMaterial`, `OrthographicCamera`, `Path`,
`Plane`, `Scene`, `ShaderMaterial`, `Shape`, `WebGLRenderer`.

The remaining imports — `DoubleSide`, `LinearFilter`, `NoToneMapping`, `PCFShadowMap`,
`SRGBColorSpace`, `UnsignedIntType` — are exported **constants**, not classes. For those only
existence matters, and it's settled above.

## What this diff does not cover

The comparison was **method-level on class bodies**. It will not catch:

- property renames or default changes (that's how the whole `outputEncoding` disaster hides);
- constructor signature changes;
- material property expansion — e.g. `MeshLambertMaterial` gained map slots across these 48
  releases without gaining methods;
- shader/`onBeforeCompile` chunk renames, which matter a great deal here — see
  `material-injection-and-triplanar.md`.

Treat a clean method diff as "no _method_ broke," not "safe to paste."

## Reproducing this

`vendor-imports.json` is generated from CAPRICCIO's real imports, so it drifts as the project
grows. To re-check after it changes, diff the exported symbols and class bodies of the two
`node_modules/three` builds directly — that's how every fact above was produced, and it beats
trusting either the docs or this file's shelf life.
