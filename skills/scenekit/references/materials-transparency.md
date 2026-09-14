# Materials, transparency, reflections

## Lighting models — and why the choice constrains everything after

`SCNMaterial.lightingModel` decides which of the material's properties do
anything at all. This is the most common source of "I set that property and
nothing happened."

| Model               | Uses                                                                                                                              | Ignores                                       |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `.physicallyBased`  | `diffuse`, `roughness`, `metalness`, `normal`, `clearCoat` (iOS 13+); reflections come from the **scene's** `lightingEnvironment` | `specular`, `shininess`, largely `reflective` |
| `.blinn` / `.phong` | `diffuse`, `specular`, `shininess`, `reflective`, `fresnelExponent`                                                               | `roughness`, `metalness`                      |
| `.lambert`          | `diffuse` only                                                                                                                    | all specular                                  |
| `.constant`         | `diffuse` only, unlit                                                                                                             | all lighting                                  |

**The practical consequence:** `fresnelExponent`, `specular`, `shininess` and
`reflective` are Blinn/Phong-era controls. Under `.physicallyBased` SceneKit
derives its own Fresnel from roughness/metalness and takes reflections from
`scene.lightingEnvironment` — which is _scene-wide_, so tuning reflections for
one surface changes lighting for every PBR material you have.

Mixing models per material is fine and often the right answer: keep the scene
PBR, and switch one surface (water, glass, a chrome prop) to `.blinn` so its
reflection controls are local to it.

## Fresnel and reflections

- `material.reflective` — a `SCNMaterialProperty` taking a sphere map or a
  6-image cube map. The header is explicit: **"The surface will not actually
  reflect other objects in the scene"** — it's a precomputed environment only.
  `reflective.intensity` scales it.
- `material.fresnelExponent` — defaults to **0**, i.e. off. Modulates
  reflectivity by view angle; higher values concentrate reflection toward
  grazing angles. This is the defining look of water, glass and polished floors.

For _real_ reflections of scene geometry there is exactly one built-in option:
**`SCNFloor`** (declared in `SCNParametricGeometry.h`), with `reflectivity`,
`reflectionFalloffStart` / `reflectionFalloffEnd`, and
`reflectionCategoryBitMask` (iOS 10+) to choose what reflects. It also gained
`width`/`length` in iOS 10, so it needn't be infinite. Costs an extra render
pass, and you give up control of its tessellation — which matters if you wanted
a vertex-displacement modifier on it.

### Fresnel does much less under an orthographic camera

Fresnel is a function of the angle between view and normal. Under an
**orthographic** projection the view vector is _identical at every pixel_, so if
the camera pitch is also fixed, the only thing varying the Fresnel term across a
flat surface is the surface normal itself. Gentle waves deviate a few degrees,
so Fresnel contributes an almost uniform tint rather than variation.

It still changes the overall look (a richer, deeper colour), but do not expect
it to produce the sparkle it gives in a perspective game with a moving camera.

## Transparency

```swift
material.transparency = 0.72        // 1.0 = opaque
material.blendMode = .alpha
material.writesToDepthBuffer = false
node.renderingOrder = 100           // draw after opaque geometry
```

The last two are not optional:

- **`writesToDepthBuffer = false`** — otherwise the transparent surface writes
  depth and occludes everything behind it, which is the exact thing you were
  trying to see through.
- **`renderingOrder`** raised — so it draws after opaque geometry and blends
  over it, rather than blending over the background.

`transparencyMode` also exists: `.aOne` (default, alpha channel), `.rgbZero`
(luminance), `.singleLayer`, and `.dualLayer` for transparent convex solids
where you want to see both faces correctly ordered (iOS 11+).

### Faking depth absorption without the depth texture

Real water darkens with depth. Since shader modifiers cannot sample scene depth
(see `shader-modifiers.md`), the cheap approximation is to tint the _submerged
geometry_ itself with a darker material.

**Caveat learned the hard way:** classify by height and you get a hard colour
step exactly along the waterline, which reads as a seam rather than as depth.
Either accept the water's own alpha doing the darkening continuously, or fade
the tint over a band rather than switching at a threshold.

## One geometry, several materials

`SCNGeometry(sources:elements:)` takes multiple `SCNGeometryElement`s that share
vertex sources, each drawing its own subset of indices with its own material —
`geometry.materials[i]` pairs with `elements[i]`.

This is the efficient way to give parts of a mesh different looks (top faces vs
walls vs ramps): one vertex buffer, one node, N draw calls, no duplicated
vertices. Build the index arrays by whatever rule you like — face normal, height,
material id — while walking the triangles.
