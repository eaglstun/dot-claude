---
semantic_id: "sOQJZW4xNQ3wybPiOGHnsNXbInZa8AAF"
related_ids:
  - "sMDBZWYxNZ_2ybJjvmGvclTzEkda4AAH"
  - "sOdjSW41uZ3G7ZqgsCHn4tV8GiZL0AAP"
---
# Reality Composer Pro 3 — release state and known issues

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/reality-composer-pro-release-notes>
- <https://developer.apple.com/documentation/realitycomposerpro/reality-composer-pro-beta-2-release-notes>
- <https://developer.apple.com/documentation/realitycomposerpro/reality-composer-pro-beta-3-release-notes>
- <https://developer.apple.com/documentation/realitycomposerpro/reality-composer-pro-beta-4-release-notes>

Fetched: 2026-08-19. **Beta 4 is the newest release note published.**

## Release state

Reality Composer Pro 3 is a **standalone app downloaded from the Apple Developer website —
no longer part of Xcode.** It requires **Apple silicon** and **macOS Tahoe 26.5 or later**.
It is in **beta**.

Check the newest release notes page before trusting anything below — this is the state as of
Beta 4, and beta-to-beta churn here is real.

## Still open at Beta 4

| Area | Issue | Workaround | ID |
| --- | --- | --- | --- |
| General | **Asset Generation is macOS 27 only** | Update to macOS 27 | 178159978 |
| Materials | Subsurface scattering (SSS weight > 0) with specular roughness < 1 **renders black** on surfaces facing away from a directional or spot light. Affects RealityKit PBR **and** OpenPBR surface nodes, when lighting descriptors are left **Unspecified** | ShaderGraph Material Descriptor Inspector → Lighting Model **Lit**, Specular Model **GGX** or **GGX Anisotropy** | 180306610 |
| Script Graph | **"On Initialize" can fail to start animation or audio** on build and run | Use **"On Activate"** instead | 182533099 |
| Scripting / Shaders | Using **world position** shifts content relative to the world origin in **shared space** apps | Use relative position, or compute your content's relationship to the world origin and adjust. See the *Squirrel* sample | 178279067 |
| RealityKit | **`ComputeGraphComponent` instances stored in a `.reality` file do not render** when the app loads it | — | 177674901 |
| Preview on visionOS | Textures may not load, leaving objects flat grey | Enter immersive mode, then exit it | 182734493 |

## Fixed along the way — useful if you're on an older build

**Beta 4 fixed:** `clearcoat` hiding specular occlusion (175159311) · lightmaps on cube and
box primitives (176278045) · **the Particle Emitter preset menu is back** — Fireworks,
Impact, Magic, Rain, Snow, Sparks (165089607).

**Beta 3 fixed:** "Assistant for ShaderGraph" needing a restart (177106224) · the Portal
preview panel failing to refresh on shader-type switch (177742196) · graph variables wrongly
appearing in ShaderGraph (178161668) · nodes missing title and description (178162061) · LOD
Generator / mesh simplification glitching with baked lighting (174362762) · **"Run with
Xcode" exports no longer requiring macOS 27** (178199201).

**Beta 2 fixed:** surface shading features (subsurface scattering, bent normals, clearcoat)
having no effect when the Descriptor toggle was "Unspecified" — Unspecified now correctly
infers configuration from the connected Shader Graph (177758292) · AI models for 3D object
and texture generation downloading incorrectly (178649074) · **plugin support** (178086142)
· **Reality Composer Pro Preview** for visionOS (178172509).

## Long-lived issue that spans every beta

**Audio requires the Audio Library component to be on the same entity as the audio source**
(174520828). Put an Audio Library on every entity carrying a Spatial, Ambient, or Channel
Audio component. This **contradicts** the audio documentation's claim that any entity can
play from any library — on current builds, believe the release note. Covered in
`audio.md`.

## Two documentation pages Apple links but hasn't published

Both 404 as of this fetch:

- `automating-motion-path-creation-with-editor-scripting-commands` — building a Motion Path
  programmatically with editor scripting commands. Linked twice from the multi-track
  animation article.
- `NavigationMeshLayers` — the details on Layers, Areas, and Flags. Linked twice from the
  navmesh article.

Editor scripting commands are clearly real — the auto-play article names
`edit_entry_in_animation_library_component` by name — but their reference isn't up.
