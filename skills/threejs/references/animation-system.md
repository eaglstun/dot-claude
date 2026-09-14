---
semantic_id: "cMSY9ylTB0cZ2QpIcEqvUikNfIe5IAAL"
related_ids:
  - "BODE5nU53h-bmQtYcEqiUtlY-qO2AAAC"
  - "TsAQGOxT0AeZWDpidQ9rV_FZbqdZEAAB"
---
# Animation System (`AnimationMixer` / `AnimationClip` / `AnimationAction`)

Source: [threejs.org manual — Animation System](https://threejs.org/manual/#en/animation-system).
This is core API that's been stable since a 2015 rewrite (Unity/Unreal-style architecture) —
applies unchanged to **both r132 and r180**. Neither project currently uses it (see the note
on the phone-in-headset project's actual convention at the bottom).

## The pieces

- **`AnimationClip`** — the data for one activity of an object (a walk cycle, a jump, a wave).
  Comes back from a loader's `animations` array on an imported animated model (skinned/rigged
  or morph-target). A model can have several clips; pick one with
  `THREE.AnimationClip.findByName(clips, 'name')`.
- **`KeyframeTrack`** — inside a clip, one track per animated property (e.g. one bone's position
  over time, a different track for that bone's rotation, another for a morph target's influence).
  A clip is just a bundle of these tracks.
- **`AnimationMixer`** — the actual player. One mixer per animated object; it blends/merges
  multiple simultaneous animations on that object like a real mixer console. Must be ticked
  every frame: `mixer.update(deltaSeconds)`.
- **`AnimationAction`** — the control surface for a clip on a mixer: play/pause/stop, loop count,
  fade in/out, time-scale/warp, crossfade, sync with other actions. Get one via
  `mixer.clipAction(clip)`.
- **`AnimationObjectGroup`** — share one animation state across a group of objects at once.

## Minimal usage

```js
let mesh;

// Create an AnimationMixer, and get the list of AnimationClip instances
const mixer = new THREE.AnimationMixer(mesh);
const clips = mesh.animations;

// Update the mixer on each frame
function update() {
  mixer.update(deltaSeconds);
}

// Play a specific animation
const clip = THREE.AnimationClip.findByName(clips, "dance");
const action = mixer.clipAction(clip);
action.play();

// Play all animations
clips.forEach(function (clip) {
  mixer.clipAction(clip).play();
});
```

## Loader support

Not every format carries animation (OBJ notably doesn't), and not every loader surfaces
`AnimationClip` sequences even when the format could. Loaders that do: `ObjectLoader`,
`BVHLoader`, `ColladaLoader`, `FBXLoader`, `GLTFLoader`. 3ds Max/Maya can't export multiple
non-overlapping-timeline animations into one file — you'll get separate exports per clip from
those tools.

## This is not what the phone-in-headset project uses

That project's animated props (moon, neon sign, truck trails, etc.) don't touch
`AnimationMixer` at all — they use a hand-rolled `group.userData.update(t, intensity)` convention
that the render loop calls directly each frame (see
`references/visual-effects-without-postprocessing.md`, "Animation conventions"). Reach for the
real `AnimationMixer` system only when driving clips off an **imported** rigged/morph-target
model (glTF character animation, etc.) — for hand-built procedural props in that project, keep
using the existing `userData.update` pattern instead of introducing a second animation system.
