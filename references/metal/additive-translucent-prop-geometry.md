---
topic_id: "v2:LHEC"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "x_M0SG8UQreJxDok6QwK95WYS4xEcAAD"
related_ids:
  - "J_2kLm9VQjcd_Asr4Sgr9qHpOsniUAAP"
  - "xfMyKG4UYqd1lnJjWlk5ZuGwIr6IcAAC"
---
# Additive, self-illuminated translucent prop geometry (volumetric beam / glow)

Drawing a glowing translucent prop (a spotlight beam shaft, a glow volume) that lives in the 3D
scene alongside opaque props, WITHOUT it shading or occluding anything else.

Sources:

- `ios/KaraokeVR/Passthrough.metal` — `beamVertex` / `beamFragment` / `BeamUniforms` (the par-can
  beam shader); `cubeVertex` / `CubeVertex` (the `[x,y,z,1,r,g,b,a]` vertex layout it reuses).
- `ios/KaraokeVR/StereoARRenderer.swift` — `beamPipeline` blend setup (in `buildPipelines`),
  `beamDepth` state (in `buildDepthStates`), `drawBeam(...)`, `beamBrightness(...)`.
- `ios/KaraokeVR/Models/ParCanBeam.swift` — the cone geometry + per-vertex alpha gradient.
- Web sibling it ports: `assets/threejs/spotlight-cone.js` (AdditiveBlending, depthWrite:false).
- Apple MTLRenderPipelineColorAttachmentDescriptor blend factors:
  developer.apple.com/documentation/metal/mtlrenderpipelinecolorattachmentdescriptor

## The recipe

1. **Reuse the cube vertex layout** `[x,y,z,1, r,g,b,a]` (8 floats) so no new vertex struct. Put the
   per-vertex glow INTENSITY in the `a` channel (rgb = a constant tint). `cubeFragment` ignores `a` —
   a new fragment must actually read it.

2. **Additive blend** (glows over whatever's behind it, order-independent):
   `isBlendingEnabled = true`, rgb+alpha op `.add`, src `.one`, dst `.one`.

3. **Premultiply in the fragment.** Additive blend has NO separate dst-alpha factor — `dst = src*1 +
dst*1` — so a separate per-fragment alpha does nothing on its own. Multiply rgb by the intensity in
   the shader: `return float4(in.color.rgb * a, a);`. That makes the `a` gradient (bright apex → 0 at
   the mouth) actually scale the light that lands on screen.

4. **Depth TEST lessEqual, depth WRITE OFF** — a dedicated depth-stencil state (`beamDepth`), NOT the
   opaque props' `sceneDepth` (lessEqual + write). Test-on means nearer real geometry (LiDAR prepass)
   and nearer props occlude the glow; write-off means it never occludes anything AND overlapping
   translucent triangles (nested cones) all blend regardless of draw order (no sorting needed).

5. **Fusion-safe by construction:** it's real 3D geometry drawn in BOTH eyes on the same per-eye
   `proj·eyeView·anchor·model` MVP (+ `offset*clip.w` lensShift in the vertex stage), exactly like
   every other prop. No full-drawable feedback, so the eye seam is untouched.

6. **Share one static buffer.** Identical local-space geometry across all instances; only the per-prop
   MVP differs. Build once at init, draw per prop in the scene loop (`if item.type == "..."`), mirroring
   the `drawTVScreen` pattern. Because the prop's animated MVP is reused, any prop `.motion` (e.g. a
   par-can's `.sweep`) animates the glow for free.

7. **Cheap breathing** (optional): one CPU scalar per frame (`base * swell * flicker` off the frame
   clock), passed in a uniform and folded into the alpha in the vertex stage — applied identically to
   both eyes, so still fusion-safe. Native twin of the web `update(t, intensity)`.

## Orienting a cone to an arbitrary aim (not an axis)

The web cone points down −Y; a real fixture's beam follows its aim `dir`. Build an orthonormal basis
in the plane perpendicular to `dir`: pick `upRef = (0,1,0)` (or `(1,0,0)` if `|dir.y|>0.99`), then
`right = normalize(cross(upRef, dir))`, `realUp = normalize(cross(dir, right))`. A ring point at
distance `d` along the aim, radius `r`, angle θ is `centre + dir*d + (cosθ*right + sinθ*realUp)*r`.
Use ≥3 axial rings so a `pow(1-f, k)` alpha falloff renders as a curve (vertex colours interpolate
linearly between rings). No cull mode is set in the cube path (default `.none`) → cone walls are
double-sided for free (the web `side: DoubleSide`).

## Per-frame cost

One additive pass per visible glowing prop × 2 eyes. Overdraw is the real cost: nested cones overlap,
so budget ~2–3× fill over the beam's on-screen area per prop. Keep radial/axial segment counts modest
(20 × 4 here) — it's a fragment-bound effect, not vertex-bound.
