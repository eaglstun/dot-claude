---
semantic_id: "JGziC21y2zWJnQoM4nCH3JF4G4umcAAM"
related_ids:
  - "9mihB2Qg1i0L2ZoJMDiHdJF9U4vWQAAD"
  - "4WngDnw9wSUJqQxsqhOS3pV4WLu2UAAP"
---
# Injecting shaders into Three.js materials, and triplanar surface treatment

How to give every surface in a scene a custom look **without giving up Three.js's lighting,
shadows and fog** — and how to project a pattern onto arbitrary geometry with no UVs.

**Version note:** from a desktop **r180** project (CAPRICCIO). `onBeforeCompile` exists and
behaves the same back through r13x; the shader chunk names quoted here are stable across
that range. What changes between versions is the surrounding chunk set, so always
`console.log(shader.fragmentShader)` once and confirm the anchor string exists rather than
trusting a snippet from the internet.

## Why inject instead of writing a ShaderMaterial

The obvious approach to a custom look is `ShaderMaterial`. It is usually the wrong one.

A `ShaderMaterial` starts from nothing: no lights, no shadow maps, no fog, no tone mapping,
no colour management. You reimplement all of it or do without. Most stylised renderers that
look flat and dead are flat and dead because they threw away the lighting pipeline to get a
hatch pattern.

`onBeforeCompile` patches Three.js's _own_ shader instead. Lighting, shadows and fog keep
working; only the surface treatment is yours.

```js
function createStoneMaterial(opts = {}) {
  const mat = new THREE.MeshLambertMaterial({ color: 0xffffff, fog: true });

  mat.onBeforeCompile = (shader) => {
    // 1. add your uniforms — share the objects, don't copy the values
    shader.uniforms.uHatchFreq = sharedUniforms.uHatchFreq;
    shader.uniforms.uInkCol = { value: new THREE.Color(opts.ink ?? "#241d12") };

    // 2. varyings + whatever you need out of the vertex stage
    shader.vertexShader = shader.vertexShader
      .replace(
        "#include <common>",
        `#include <common>
        varying vec3 vWorldPosE;
        varying vec3 vWorldNormalE;
        attribute vec2 aTone;      // custom per-vertex attribute
        varying vec2 vToneE;
      `,
      )
      .replace(
        "#include <fog_vertex>",
        `#include <fog_vertex>
        {
          vec4 cwp = vec4(transformed, 1.0);
          #ifdef USE_INSTANCING
            cwp = instanceMatrix * cwp;
          #endif
          cwp = modelMatrix * cwp;
          vWorldPosE = cwp.xyz;

          vec3 cwn = objectNormal;
          #ifdef USE_INSTANCING
            cwn = mat3(instanceMatrix) * cwn;
          #endif
          vWorldNormalE = normalize(mat3(modelMatrix) * cwn);
          vToneE = aTone;
        }
      `,
      );

    // 3. take over the final colour
    shader.fragmentShader = shader.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>
        varying vec3 vWorldPosE;
        varying vec3 vWorldNormalE;
        varying vec2 vToneE;
        uniform float uHatchFreq;
        uniform vec3 uInkCol;
      `,
      )
      .replace(
        "#include <opaque_fragment>",
        `
        // outgoingLight is fully lit and shadowed at this point
        float b = dot(outgoingLight, vec3(0.2126, 0.7152, 0.0722));
        vec3 surf = myTreatment(vWorldPosE, vWorldNormalE, b);
        gl_FragColor = vec4(surf, diffuseColor.a);
      `,
      );
  };

  return mat;
}
```

### The anchors worth knowing

| anchor                       | stage    | why                                                           |
| ---------------------------- | -------- | ------------------------------------------------------------- |
| `#include <common>`          | both     | top of file — declare varyings, uniforms, attributes, helpers |
| `#include <fog_vertex>`      | vertex   | late, after `transformed` and `objectNormal` are final        |
| `#include <opaque_fragment>` | fragment | `outgoingLight` is complete: lit, shadowed, everything        |

Reading `outgoingLight` rather than recomputing lighting is the whole trick. Collapse it to
a scalar and you have a shading _level_ to drive a pattern with, while Three.js keeps doing
the hard part.

### Two gotchas that will cost you an afternoon

**1. Materials with `onBeforeCompile` share a program cache key.** Two materials with
different injected _code_ but the same base type can collide and one silently gets the
other's shader. If your variants branch on code rather than uniforms, set:

```js
mat.customProgramCacheKey = () => "stone-" + variantName;
```

**2. `#ifdef USE_INSTANCING` is not optional.** Forget it and everything renders correctly
as normal meshes and wrongly on `InstancedMesh` — geometry drawn at the origin, or lit as if
it were. Instanced crowds are exactly where this bites, and the symptom looks like a
transform bug rather than a shader bug.

## Custom per-vertex attributes

`aTone` above is a custom attribute — two floats per vertex carrying a tone bias, so
different parts of one merged mesh can shade differently without splitting the draw call.

```js
function setToneAttribute(geo, a = 1, b = 0) {
  const n = geo.attributes.position.count;
  if (!geo.attributes.aTone || geo.attributes.aTone.count !== n) {
    const arr = new Float32Array(n * 2);
    for (let i = 0; i < n; i++) {
      arr[i * 2] = a;
      arr[i * 2 + 1] = b;
    }
    geo.setAttribute("aTone", new THREE.BufferAttribute(arr, 2));
  }
}
```

**Every geometry the material touches must have the attribute.** A missing custom attribute
does not throw — the shader reads garbage, and you get one mesh in the scene rendering
wrong. Run all geometry through one helper so it cannot be forgotten.

## Triplanar projection — patterning without UVs

Procedural geometry rarely has sensible UVs, and unwrapping a merged city is not a project
anyone wants. Triplanar sidesteps it: sample the pattern three times in world space, once
per axis plane, and blend by the squared normal.

```glsl
float triplanar(vec3 wp, vec3 n, vec2 dir, float freq) {
  vec3 aw = n * n;                      // already sums to 1 for a unit normal
  return aw.z * pattern(wp.xy, dir, freq)
       + aw.x * pattern(wp.zy, dir, freq)
       + aw.y * pattern(wp.xz, dir, freq);
}
```

Any surface at any angle gets clean coverage with no seams and no UVs.

**World space, not view space.** This is the part that matters. Because the coordinate is
the world position, the pattern is _anchored to the surface_ — move the camera and it stays
put on the stone, the way ink sits on paper. Sample in screen space instead and the pattern
crawls across the image as you orbit, which instantly reads as a filter laid over the scene
rather than a property of it.

### Distance-adaptive frequency

A fixed-frequency world-space pattern aliases badly at distance — it gets finer on screen as
it recedes until it turns to moiré. Fix it the way mipmapping does, manually: evaluate at
two frequencies an octave apart and crossfade.

```glsl
float lv = log2(max(distanceToCamera, 1.0));
float lf = fract(lv);
float a = triplanar(wp, n, dir, freq * exp2(floor(lv)));
float b = triplanar(wp, n, dir, freq * exp2(floor(lv) + 1.0));
float result = mix(a, b, lf);
```

Stroke density then stays roughly constant in screen space while remaining locked to the
surface — the detail that separates this from a shader-toy effect.

Add a little noise to the coordinate before rasterising if the pattern should look
hand-made:

```glsl
s += (noise(co * 0.31) - 0.5) * wobble;
```

Perfectly straight lines read as machine-ruled. A small wobble reads as a hand.
