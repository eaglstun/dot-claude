---
semantic_id: "okdJYcYdt13ubbvyNiOP4tOeAndK8AAK"
related_ids:
  - "IGQLSe5Vv8lYbfoysmOP8lI-ClJK8AAK"
  - "sOQJZW4xNQ3wybPiOGHnsNXbInZa8AAF"
---
# Audio — components, assets, and what each one costs

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/introduction-to-reality-composer-pro-audio>
- <https://developer.apple.com/documentation/realitycomposerpro/optimizing-audio-playback>

Fetched: 2026-08-19

## Import and inspect

Project Browser → **Import Asset**, or drag from Finder. Click an audio file, then **Play**
in the Preview tab (which shows channels above the waveform).

Inspector properties (see `AudioFileResource.Configuration`):

- **Should Loop** — seamless, sample-precise looping. **Looping via the API's
  `completionHandler` leaves a slight gap between repeats;** configuring it on the resource
  lets the audio engine guarantee seamlessness.
- **Should Randomize Start** — randomizes the start time.
- **Should Stream** — stream from disk instead of loading into memory. Saves memory, costs
  compute.

**Should Randomize Start + Should Loop together** give you variation from a single file —
useful for constant ambience with subtle change. Add multiple instances of the same file for
more variation still.

## The three playback components

They differ in how they respond to listener **position** and **orientation** — and in cost.

| Component | Position | Orientation | Reverb | Use for |
| --- | --- | --- | --- | --- |
| **Spatial Audio** *(default)* | Yes — distance attenuation | Yes | **Inherits scene reverb** | Sound emanating from a specific entity |
| **Ambient Audio** | **No** — volume doesn't change with distance | Yes — channels shift as entity or listener rotates | No; relies on reverb baked into the source file | Multichannel field recordings of outdoor environments |
| **Channel Audio** | No | No — left is always left | No | Music and other non-spatialized audio routed straight to device output |

**Spatial Audio is what you get by default.** If you never explicitly choose a component,
every audio-emitting entity pays the highest per-voice cost, without anyone having decided
that.

Cost, most to least expensive:

1. **Spatial Audio** — tracks the emitting entity's position and orientation relative to the
   listener, computes distance attenuation, mixes to mono, applies directivity, sends to
   reverb.
2. **Ambient Audio** — applies orientation, but no distance attenuation and no reverb send.
3. **Channel Audio** — straight to output channels, none of the above.

Types: `SpatialAudioComponent`, `AmbientAudioComponent`, `ChannelAudioComponent`.

> **Spatial audio sources are negative-Z forward** — represented in the component by the
> yellow arrow. If you authored source content facing **positive-Z** *and* you use a
> non-default `directivity` (a `.beam(focus:)` with non-zero focus), **rotate the source
> entity 180° around y** or the beam points backwards. The default
> `.beam(focus: .zero)` radiates evenly and needs no rotation.

## Loading strategy — memory vs. compute

`AudioFileResource.LoadingStrategy`, exposed in RCP as the **Should Stream** toggle:

| Strategy | Behavior | Right for |
| --- | --- | --- |
| **`.preload`** | Decodes the whole asset into memory up front | Short, frequent, latency-sensitive sounds — UI feedback, footsteps, gunshots. Decode happens once; per-play CPU is low and predictable |
| **`.stream`** | Decodes incrementally from disk during playback | Long assets — music beds, ambiences, voice-over. Low memory, but decoding continues on the audio thread for the whole duration |

**The interaction that's easy to miss:** the `.dynamic` case of `AudioResource.Normalization`
applies real-time dynamic compression. On a `.preload` resource that work happens **once**, at
load. On a `.stream` resource it runs **continuously alongside the ongoing decode** — two
per-frame costs stacked on the audio thread instead of one. If a streamed asset also needs
loudness normalization, weigh that against just preloading it.

## Tuning SpatialAudioComponent

`gain`, `directLevel`, `reverbLevel` — all relative decibels in
`[-Decibel.infinity, Decibel.zero]`:

- **`gain`** — overall output level.
- **`directLevel`** — level of the direct, unreverberated signal reaching the listener.
- **`reverbLevel`** — level sent to the reverb system. Setting it to `-Decibel.infinity`
  removes the reverb send entirely, collapsing the sound fully dry. **This is the only one of
  the four that genuinely reduces engine workload.**
- **`directivity`** (`Audio.Directivity`) — how sound radiates. `.beam(focus:)` models a
  parametric, frequency-dependent pattern where `focus` sets beam width.
- **`distanceAttenuation`** (`Audio.DistanceAttenuation`) — `.rolloff(factor:)` for a custom
  falloff curve, or `.default`.

> **Treat `directivity` and `distanceAttenuation` as realism controls, not cost controls.**
> A narrow beam or custom rolloff changes how the sound behaves; it doesn't reduce the work
> the engine does.

## Author mono for spatial audio

Spatial audio sources are **single-channel only** — `SpatialAudioComponent` mixes any source
down to mono before spatializing it. Because that happens automatically it's tempting to
import stereo and let the engine sort it out. **Author and export mono directly instead:** it
avoids phase-cancellation artifacts from the collapse, and keeps files smaller on disk, which
also shrinks the memory cost of preloading.

## Reverb

Add a **Reverb component** to define a scene-wide preset — Living Room, Concert Hall, etc.

- **Only one can be active at a time** in a scene (per `ARView`/`RealityView` on macOS and
  iOS). Place it on a high-level entity; it affects every entity with a Spatial Audio
  component.
- Reverb is a **shared, scene-wide system**, not something each sound carries. `reverbLevel`
  is the per-sound lever on that shared cost.

> **visionOS exception:** `ReverbComponent` is active **only while your app has a progressive
> or full immersive space open.** In Shared Space or a mixed immersion style, RealityKit uses
> real-environment acoustics simulation and **ignores `ReverbComponent` entirely.** If you're
> tuning `reverbLevel` or `directLevel` expecting your preset to shape the sound, check your
> immersion style first — outside an immersive space the preset does nothing.

## Audio File Groups vs. Audio Mix Groups

Similar names, unrelated jobs.

**Audio File Group** — a collection of variations (footsteps, bird calls). **RealityKit plays
a random file from the group.** Project Browser → **`+` → Audio → Audio File Group** → name →
in the Inspector set **Sound** under **Audio File Asset** → **`+`** next to **Assets** for
more. Any number per project. Grouping variations this way beats authoring and referencing
several near-identical assets individually, for both project structure and memory footprint.

**Audio Mix Group** — centralized runtime volume and speed control for a related set of
sounds behind a single slider. **Add only one to your scene**, on a top-level entity. Project
Browser → **`+` → Audio → Audio Mix Group** → name → Inspector → **Sounds** → **Add Sound**.
In code, `mixGroupName` on `AudioFileResource.Configuration` assigns a resource to a group.
Routing sounds through one means your app manages a single control surface instead of holding
an `AudioPlaybackController` per sound.

## Audio Library Component

References named sounds directly, or an Audio File Group for random selection. Other
systems — Script Graphs, Animation Sequences — reference audio through it.

Select an entity → Inspector → **Add Component → Audio Library** → **`+` Named Audio
Reference** → set **Name** and **Audio Asset** → repeat.

**An Audio Library does not have to be played from the entity it's attached to** — any entity
can reference and play files from it.

> **Known issue (all RCP 3 betas, 174520828):** in practice, **audio requires the Audio
> Library component to be on the same entity as the audio source.** Workaround: put an Audio
> Library on every entity that has a Spatial, Ambient, or Channel Audio component, holding
> the files that entity plays. This contradicts the "any entity can play from any library"
> guidance above — believe the release note on current builds.

## Preparation and playback cost

`prepareAudio(_:)` readies a resource — and readiness isn't free. Apple's own wording: *"As
soon as the system prepares an audio resource, the audio engine begins tracking the position
of the entity and allocates rendering resources, which incurs a power cost."* And: *"For
optimal system resource usage, avoid preparing sounds before they are needed."*

**`playAudio(_:)` calls `prepareAudio(_:)` internally** before `play()`, so the cost lands the
instant you call it. There is no way to play a sound without paying preparation.

Two ways that compounds:

- **Calling `playAudio(_:)` repeatedly without checking `isPlaying` starts a new playback
  instance each time**, each with its own tracking and rendering allocation running
  concurrently.
- **Preparing or playing on an entity not yet parented in the scene still costs** tracking and
  allocation, even though nothing is audible.

That second point rules out the intuitive-but-wrong optimization: preparing audio as a
"warm-up" before placing an entity. Playback only starts once the entity is parented and
placed, so preparing early saves nothing — it just starts the power cost sooner.

## Change a playing sound, don't restart it

Starting playback returns an **`AudioPlaybackController`**. Use it instead of stopping and
re-triggering `playAudio(_:)`:

- `fade(to:duration:)`, `speed`, `reverbSendLevel`, `seek(to:)`, `play(at:)` — adjust a
  playing sound **in place**, without paying tracking and allocation for a new instance.
- `stop()`, `pause()`, `isPlaying` — control and query state.

**Check `isPlaying` before calling `playAudio(_:)` again on the same entity.**
