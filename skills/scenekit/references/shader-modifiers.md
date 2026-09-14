# Shader modifiers

Snippets of GLSL/MSL injected into SceneKit's own shader program. The cheap way
to customise rendering without writing a whole `SCNProgram` and losing lighting,
shadows and the rest of the pipeline.

Set on `SCNMaterial` (or `SCNGeometry`) via `shaderModifiers: [entryPoint: source]`.

## The four entry points

Run in this order (`SCNShadable.h:97`):

| Entry point                                | Stage    | Typical use                                       |
| ------------------------------------------ | -------- | ------------------------------------------------- |
| `SCNShaderModifierEntryPointGeometry`      | vertex   | Displace positions/normals — waves, wind, bulges  |
| `SCNShaderModifierEntryPointSurface`       | fragment | Change diffuse/normal/roughness _before_ lighting |
| `SCNShaderModifierEntryPointLightingModel` | fragment | Replace the lighting equation itself              |
| `SCNShaderModifierEntryPointFragment`      | fragment | Final tweak of `_output.color` _after_ lighting   |

Choosing between `surface` and `fragment` matters: a colour grade applied at
`surface` gets lit afterwards, at `fragment` it doesn't. For an effect that
should apply uniformly regardless of lighting (distance fog, desaturation,
tinting), use `fragment`.

## Structure

```
#pragma arguments
float myAmplitude;
float3 myTint;

#pragma body
_geometry.position.z += sin(_geometry.position.x) * myAmplitude;
```

`#pragma arguments` declares custom uniforms; `#pragma body` is the code. On iOS
this is **Metal Shading Language**, so use `float3`/`float4`, not `vec3`/`vec4`.

## Built-in uniforms — the complete list

Verified in `SCNShadable.h`. This is _everything_ SceneKit provides:

**Frame** — `scn_frame.time` (seconds), `scn_frame.inverseResolution`
(1.0 / screen size), `viewTransform`, `inverseViewTransform`,
`projectionTransform`, `inverseProjectionTransform`.

**Node** — `scn_node.normalTransform`, `modelTransform`, `inverseModelTransform`,
`modelViewTransform`, `inverseModelViewTransform`,
`modelViewProjectionTransform`, `inverseModelViewProjectionTransform`,
`boundingBox`, `worldBoundingBox` (both `float2x3`, min then max corner).

**Note `scn_frame.time` exists** — self-animating effects need no per-frame CPU
work at all.

### What is NOT available: the scene depth texture

There is no depth-buffer binding in that list. This rules out, from a shader
modifier alone:

- soft particles / depth-faded intersections
- foam or shoreline lines where a water plane meets terrain
- transparency that thickens with depth (water absorption)
- refraction of what's behind a surface
- screen-space anything that needs scene depth

All of those require an `SCNTechnique` with a custom depth pass, which is a
substantially bigger undertaking. Budget accordingly before promising them.

`_surface.position` **is** available in fragment/surface modifiers and is in
**view space**, so `-_surface.position.z` gives distance along the view axis.
That's enough for distance fog, depth-based tinting, and aerial perspective —
just not for anything comparing against _other_ geometry.

## The trap: assigning `shaderModifiers` clears your uniforms

Custom uniforms are bound by KVC: declaring `float myAmplitude` makes SceneKit
observe the material's `myAmplitude` key, set with
`material.setValue(NSNumber(value:), forKey: "myAmplitude")`.

**Assigning `material.shaderModifiers` rebuilds the program and drops values set
before that assignment.** Two ways this bites:

```swift
// BROKEN — the second assignment wipes the first modifier entirely
material.shaderModifiers = [.geometry: waveCode]
material.shaderModifiers = [.fragment: tintCode]

// BROKEN — the value is set, then discarded by a later reassignment
material.setValue(NSNumber(value: 0.2), forKey: "waveAmp")
material.shaderModifiers = [.fragment: tintCode]   // waveAmp is now unset
```

Correct:

```swift
var modifiers = material.shaderModifiers ?? [:]
modifiers[.fragment] = tintCode
material.shaderModifiers = modifiers
// ...then (re)set every uniform AFTER the last assignment.
```

**It fails silently.** No warning, no compile error — the shader just runs with
zeros, which for a displacement modifier means a perfectly flat surface that
looks intentional. If a shader-modifier effect "does nothing", suspect this
before suspecting the shader.

The robust fix for anything animated is to push _all_ of its uniforms every
frame rather than once at construction. Three KVC sets per frame is free, and
ordering can never break it again.

## Verifying an effect actually runs

Screenshots lie — a static-looking effect may be a working shader with a subtle
result, or a dead shader. Measure:

- **Is it animating?** Diff two frames restricted to the affected region. Watch
  for a confound: if the camera or anything else moved between captures, the
  whole frame differs and tells you nothing.
- **Is the shape there?** For displacement, sample luma variance _along a line of
  constant depth_. Under a fixed camera, a smooth depth gradient cannot vary
  along such a line, so the remaining variation is your effect.
- Beware other explanations for variation. A cast shadow falling on a flat plane
  can look convincingly like wave shading in a still.
