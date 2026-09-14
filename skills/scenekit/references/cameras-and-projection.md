# Cameras and projection

## Orthographic setup

```swift
camera.usesOrthographicProjection = true
camera.orthographicScale = 9          // HALF the visible world height
camera.zNear = 1
camera.zFar = 400
```

**`orthographicScale` is half the viewport height in world units**, and it is the
*only* thing controlling framing. Under orthographic projection the camera's
distance from its subject changes nothing about size — only near/far clipping.
That trips people who try to "zoom" by moving the camera.

Horizontal extent follows from the viewport aspect:
`halfWidth = orthographicScale * (viewWidth / viewHeight)`.

For perspective cameras, `projectionDirection` (`.vertical` / `.horizontal`)
decides which axis `fieldOfView` refers to. In portrait, `.vertical` with a
narrow FOV leaves almost nothing visible horizontally — pick the axis that is
actually scarce.

## True isometric

Orthographic projection plus a pitch of **atan(1/√2) ≈ 35.264°**. At exactly that
angle the three world axes project 120° apart and a unit cube's top face reads as
a regular rhombus. Any other pitch is dimetric — the classic "2:1 pixel art"
look is 30°, which is *not* isometric despite the name.

## What orthographic projection takes away

Worth knowing before designing around it, because these surprise people who have
only used perspective cameras:

- **No horizon.** An infinite horizontal plane fills the *entire* screen: every
  ray is parallel and pitched downward, so all of them hit it. There is no
  vanishing line to hide a plane's edge behind. To show sky beyond a ground or
  water plane you must make it finite and fade its rim.
- **No convergence and no size falloff.** Distant objects are drawn exactly the
  same size as near ones. Depth must be carried by other channels — cast shadows,
  colour/saturation gradients, occlusion.
- **A constant view vector.** Every pixel shares one view direction, so anything
  that depends on view angle (Fresnel, specular, rim lighting) varies only with
  the surface normal. Effects that rely on view-angle variation across a surface
  do far less than expected. See `materials-transparency.md`.

## Driving the camera by hand

To position a camera without `look(at:)`, build the transform directly. SceneKit
cameras look down their **-Z**:

```swift
var m = matrix_identity_float4x4
m.columns.0 = SIMD4(right, 0)
m.columns.1 = SIMD4(up, 0)
m.columns.2 = SIMD4(-forward, 0)   // negated: -Z is the view direction
m.columns.3 = SIMD4(position, 1)
node.simdTransform = m
```

Guard the degenerate case where `forward` is near-parallel to the reference up
vector (looking straight down) by swapping the reference axis. Rolling the
reference up-vector about `forward` before building the basis gives a dutch
angle for free.

## Depth in view space

`_surface.position` in a fragment shader modifier is **view space**, so
`-_surface.position.z` is distance along the view axis. For an effect meant to
span the visible depth range, derive the range rather than hard-coding it:

```
halfVisibleDepth = orthographicScale / tan(pitch)
```

(Half the screen height is `orthographicScale` world units; the ground is tilted
by `pitch` relative to the view plane, so that screen extent covers
`scale / sin(pitch)` of ground, which shifts view-axis depth by `× cos(pitch)`.)

Hard-coded ranges silently waste most of their gradient off-screen — an effect
tuned to "0.35 strength" can measure as 19% because half the ramp fell outside
the view.
