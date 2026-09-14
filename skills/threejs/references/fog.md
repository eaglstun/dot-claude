---
semantic_id: "LeUiP2Wxs1sZbY0L8FmH2OF6WsGPEAAJ"
related_ids:
  - "JGziC21y2zWJnQoM4nCH3JF4G4umcAAM"
  - "IE2i8TWxQxcJiStuYDgz6lncOsGzEAAN"
---
# Fog (`THREE.Fog` / `THREE.FogExp2`)

Source: [threejs.org manual — Fog](https://threejs.org/manual/#en/fog). Long-stable core API —
applies unchanged to **both r132 and r180**. Neither project currently sets scene fog.

## The two types

Fog fades rendered pixels to a color based on distance from the camera. Set it on
`scene.fog`:

- **`THREE.Fog(color, near, far)`** — linear. Nothing closer than `near` is affected; anything
  past `far` is fully the fog color; the band between fades linearly. The common choice, since
  you can pick exactly where the clear zone ends.
- **`THREE.FogExp2(color, density)`** — exponential falloff with distance. Physically closer to
  real fog, but no explicit near/far to tune.

```js
const scene = new THREE.Scene();
{
  const color = 0xffffff; // white
  const near = 10;
  const far = 100;
  scene.fog = new THREE.Fog(color, near, far);
}
```

```js
const scene = new THREE.Scene();
{
  const color = 0xffffff;
  const density = 0.1;
  scene.fog = new THREE.FogExp2(color, density);
}
```

## Background color must match

Fog only affects _rendered_ pixels — it's part of each fragment's color calculation. Empty space
(the canvas background) doesn't get fogged on its own. To make a scene fade to a color at
distance, set **both** `scene.fog` and `scene.background` to the same color, or the horizon reads
as a hard-edged wall of fog color against a differently-colored void:

```js
scene.background = new THREE.Color("#F00"); // red
```

## Per-material opt-out

`material.fog` (boolean, defaults `true` on most materials) controls whether that material is
affected by scene fog at all. Turn it off for things that shouldn't fade — e.g. cockpit/vehicle
interior geometry when the camera is inside it, or a house interior where the far wall of a room
is closer than the fog's `far` distance but would otherwise visibly fog out against the "outside
looks foggy" effect.

## Tuning feel

`near`/`far` set the transition band width relative to what's actually in view — e.g. with the
camera ~2 units from a subject, `near=1.9, far=2.0` gives an almost-binary cutoff, while
`near=1.1, far=2.9` gives a smooth gradual fade. Pick values relative to your scene's actual
camera-to-subject distances, not fixed absolute numbers.
