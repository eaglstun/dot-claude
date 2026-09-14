# Lighting and shadows

## Shadow settings that matter

```swift
light.castsShadow = true
light.shadowMode = .forward          // or .deferred
light.shadowMapSize = CGSize(width: 4096, height: 4096)
light.shadowSampleCount = 48         // PCF taps
light.shadowRadius = 9.0             // PCF blur width
light.shadowColor = UIColor(...)     // alpha controls strength
light.shadowBias = 3.0
light.automaticallyAdjustsShadowProjection = true
light.shadowCascadeCount = 1
```

**`shadowRadius` and `shadowSampleCount` must move together.** The radius is the
blur width and the count is how many taps spread across it. Widen the radius
alone and the blur bands into visible rings instead of reading as soft.

**`.forward` vs `.deferred`:** deferred resolves shadows as a screen-space pass
and can add faint banding across large flat surfaces. Forward computes them in
the material shader and is generally cleaner. A/B them offscreen before
committing — the difference is subtle but consistent.

**Cascades:** `shadowCascadeCount > 1` splits the shadow map by distance. On a
small scene the split seams land in the middle of the view and read as banding.
Use 1 unless the scene is genuinely large.

**Bias fixes acne, not aliasing.** Dotted/moiré patterns on lit surfaces are
bias. *Serrated* shadow edges are resolution/blur — raise the sample count and
radius, not the bias. Pushing bias too far detaches shadows from their casters.

## The big one: shadows that render nothing

Before touching any shadow *setting*, check the light's **direction relative to
the camera**.

If the light and the camera are on the same side of the scene, every shadow
falls on the far side of its own caster and is hidden by it. The scene looks
exactly like shadows are disabled. This can consume hours of tuning bias,
radius, map size and shadow mode — none of which is the problem.

Diagnose it by rendering a minimal repro offscreen (a box on a plane, light
deliberately opposite the camera) with `SCNRenderer.snapshot(atTime:with:)`. If
shadows appear there, the setup is fine and the placement is wrong.

**For a camera that orbits 360°**, no single lateral light direction works from
every angle — half the yaws will hide the shadows. Use a **steep** light
(~70° elevation) so shadows stay short and hug each object's base, visible from
every direction. Short contact shadows also double as the "am I over the edge?"
depth cue that an orthographic view otherwise lacks.

## Keeping lighting stable while the camera spins

A world-fixed light keeps shading stable as the player rotates the view, which is
good for readability — but guarantees yaws where you're looking at nothing but
shadow sides, and the scene goes flat and dark.

Fix with a **fill light** from roughly the opposite direction, shallower, at
around a third the main light's intensity, with `castsShadow = false`. No face is
ever fully unlit, the main light stays world-fixed, and the shadows are untouched.

## Lighting categories — restricting a light to specific nodes

A light illuminates a node when their masks intersect:

```swift
light.categoryBitMask  // default: all bits set
node.categoryBitMask   // default: 1
```

So to give one object its own private light:

```swift
let special = 1 << 2
glintLight.categoryBitMask = special          // only lights matching nodes
waterNode.categoryBitMask = 1 | special       // still lit by the normal lights
```

Useful when one surface needs lighting that would be wrong for everything else —
for example a specular light aimed to make water glint toward the camera, which
can then track the camera without making the rest of the scene's shading swim.

## Specular highlights are a geometry problem first

A specular highlight requires the surface normal to bisect the view and light
directions. Before tuning `shininess`, check whether a highlight is reachable at
all:

```
required normal tilt from vertical = 90 - (light_elevation + view_elevation) / 2
```

With a 70° light and a 35° camera, the normal must tilt **37°** — far beyond
what gentle waves or a near-flat surface will ever produce. In that situation
there is no highlight anywhere on the surface at *any* shininess, and tuning is
wasted effort.

The fix is a dedicated light (see categories above) placed at the camera's own
elevation on the opposite azimuth, so a flat surface reflects it back at the
viewer and small normal deviations swing the highlight strongly.

## MSAA

`SCNView.antialiasingMode = .multisampling2X/4X`. Worth ruling in or out early
when debugging render passes, but note it was **not** the cause of missing
deferred shadows in at least one investigation — the light direction was.
