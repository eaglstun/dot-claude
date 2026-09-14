---
topic_id: "v2:DHIF"
topic_path: "model-runners/metal-skinning"
semantic_id: "XnxTGf_GEgctzVJodntHVXF0dbSEEAAB"
related_ids:
  - "Xk0bvdbWEkcN1WJodG5DB2NydLaMMAAO"
  - "bmhbtXrWUkcNxWNIIG4KV2ty9raMMAAJ"
---
# Generative 3D — rigged + animated model APIs, and the iOS runtime reality

Research 2026-06-28 (three parallel `general-purpose` research passes; the deep-research harness
had failed on a structured-output error, so this was the reliable re-run). Goal: a **fully
AI-generated** pipeline producing **rigged (skeleton + skin weights) + animated** models, for
**both humanoid and arbitrary** subjects, via **REST**, high-poly OK, consumed by the native
**hand-rolled Metal renderer (which today has NO skinning/animation)**. Ships under the LLC →
licensing matters. Claims below are vendor-doc-grounded; **verify the flagged items per-asset**.

## The shape of the space

Most services **rig+animate an existing mesh**, not text→animated-character in one call. The
realistic pipeline is two stages: **generate mesh** (Meshy/Tripo/Rodin/Hunyuan) → **rig+animate**.
Also: the turnkey services **retarget from a preset library**, they are NOT text-to-motion —
"fully AI-generated motion" in practice = library retarget. True text-to-motion exists but is
humanoid-only and rougher (Uthana, DeepMotion SayMotion, fal HY-Motion).

## Turnkey: rigged-AND-animated GLB/FBX over REST (what the pipeline wants)

| Service                      | Subjects                                                                  | Non-humanoid rig                     | REST                                          | Output (skeleton+weights+clips)                | Animation                                                             | License (commercial)                                    | Notes                                                                                          |
| ---------------------------- | ------------------------------------------------------------------------- | ------------------------------------ | --------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Tripo3D** ⭐ arbitrary     | biped, quad, hexapod, octopod, avian, serpentine, aquatic (auto-detected) | ✅ **only REST option that does it** | ✅ chained `animate_prerigcheck→rig→retarget` | ✅ **GLB/FBX**, `spec=mixamo` for Mixamo bones | ~16 presets (SDK); "100+" marketed (unverified); **no clear "dance"** | Free=CC BY 4.0; Pro/Max private+commercial              | Engine = **UniRig**. Rig 25cr/$0.25, retarget 10cr/$0.10.                                      |
| **Meshy** ⭐ humanoid        | **humanoid/biped ONLY via API** (docs explicit; reject non-humanoid)      | ❌                                   | ✅ `/rigging` + `/animations`; also on fal.ai | ✅ rigged **FBX+GLB**, `animation_glb_url`     | **~580–700 clips incl. a Dancing category**                           | Free=CC BY 4.0; Pro/Studio full ownership               | **Accepts external GLB ≤300k faces** → generate elsewhere, rig here. Cheap (rig 5cr/anim 3cr). |
| **Anything World**           | humanoid **+ animals/quadrupeds/objects**                                 | ✅                                   | ✅ `/rig` + `/animate` (poll)                 | ✅ FBX/GLB + clips                             | gait-matched library + some generated                                 | ~$50/mo, license selectable (ccby/cc0/mit) — **verify** | Best turnkey for **animals**. API "experimental, subject to change".                           |
| **Masterpiece X – Generate** | humanoid                                                                  | ❌                                   | ✅                                            | ✅ GLB/FBX/**USDZ**, rigged + basic anims      | bundled basic clips                                                   | commercial (paid)                                       | Notable: emits **USDZ** directly. Pivoting to "WorldEngen" Dec 2025 — continuity risk.         |

## Text-to-motion (humanoid only; emit a clip you retarget onto a rig)

- **Uthana** — auto-rigs any biped (<30s) then **text→motion**; FBX/GLB; GraphQL async (scriptable); Creator $16/mo commercial. Best humanoid text-driven option.
- **DeepMotion SayMotion** — true **REST text→motion**, but does **NOT rig** (you supply a rigged glTF/FBX). FBX/BVH/GLB.
- **fal `hunyuan-motion` (HY-Motion 1.0, Dec 2025)** — REST, ~$0.08/gen, **FBX + motion JSON**; Tencent community license (verify).
- **MoMask** (MIT code, BVH out) — author HF Space only.

## Open / self-host riggers (MIT/Apache; rest-pose only unless noted)

- **UniRig** (VAST/Tsinghua, SIGGRAPH'25, **MIT**) — arbitrary; GLB+FBX skeleton+weights; **no animation** (physics "coming"); unofficial Replicate port `aaronjmars/unirig-ai` (~$0.46/run). This is Tripo's engine.
- **MagicArticulate** (ByteDance, **Apache-2.0**) — arbitrary; no REST; follow-up **Puppeteer** (Aug'25) adds video-driven animation.
- **Make-It-Animatable** (CVPR'25, **MIT**) — humanoid, Mixamo target, **can apply Mixamo motion**; HF Space only.
- ❌ **Anymate** = no license (not commercial-safe); **RigNet** = GPLv3/dormant; **Hunyuan3D rig** = no public REST rig endpoint + restricted Tencent license.

## AVOID: 4D / animated-mesh generation

Animate3D, DreamGaussian4D, L4GM, SV4D, STAG4D, AnimateAnyMesh, Diffusion4D → output **Gaussian
splats / dynamic NeRF / per-frame OBJ**, NOT rigged skinned glTF, and none is a hosted REST API.
Wrong output shape for a skinning renderer. (Exception watch: **Rigel3D**, arXiv May'26, claims
image→mesh+skeleton+skinning — no code released yet.)

## PART B — the real blocker: playing a rigged/animated mesh on iOS

The native renderer draws static vertex arrays; generated output is **glTF/GLB with skin +
animations**. Paths, least-effort first:

1. **GLTFKit2 → RealityKit, composited via `RealityRenderer`→MTLTexture per eye** — _lowest code._
   GLTFKit2 (warrenm, actively maintained, **added skeletal-animation support** v0.5.x) parses
   glTF into a RealityKit `Entity`; RealityKit plays the skeletal animation; `RealityRenderer`
   renders to an `MTLTexture` you composite into each eye. ~days. **No glTF→USDZ needed.** Flags:
   verify `RealityRenderer` iOS-min (likely iOS 18); adds RealityKit to a hand-rolled app; a known
   `playAnimation`-vs-`setBlendShapes` bug.
2. **Hand-rolled Metal linear-blend skinning** — _most code (~1–3 wks), zero conversion, native
   to the per-eye pipeline._ Add `JOINTS_0`(ushort4)+`WEIGHTS_0`(float4) to the vertex format;
   per frame compute `jointMatrix[j] = inverse(modelWorld)·globalJoint[j]·inverseBind[j]` walking
   the glTF node tree; pass joints as a `device float4x4*` MTLBuffer (constant array caps ~256
   joints); skinning VS does `Σ wᵢ·jointMatrix[jᵢ]·pos`; animate via glTF channels/samplers
   (lerp T/S, slerp R, Hermite for cubicspline). **Let GLTFKit2 do only the parsing** to skip the
   biggest chunk. Gotchas: weight normalize, quat shortest-path, non-uniform-scale normals.
3. **GLTFKit2 → SceneKit** — easy (`SCNSkinner` "just works"), but SceneKit **soft-deprecated
   WWDC25**; doesn't composite into the stereo pass. Spike only.
4. **glTF→USDZ→RealityKit** — _only if USDZ independently required._ The conversion is the lossiest
   link and **skeletal animation is exactly what breaks** (usd_from_gltf is "lossy, not
   interchange"; usdzconvert discontinued). Don't make USDZ a pipeline intermediate.
5. **Model I/O** — does NOT import glTF; avoid.

**Keep assets glTF/GLB end-to-end.** USDZ is a fragile carrier for generated rigs. If you ever
need USDZ, prefer a generator that emits it directly (Masterpiece X) over converting.

## Verdict

- **Generation is solved enough today:** **Tripo3D** is the primary (only REST that rigs
  non-humanoids — covers "both"), **Meshy** for humanoid dancers (best/biggest animation library
  incl. dance, and it accepts external GLBs so you can generate anywhere and rig there). Both emit
  rigged-animated GLB/FBX over async REST.
- **The actual project is the iOS runtime, not the API.** You need a skinned-mesh player. Fast
  path = GLTFKit2 + RealityKit (RealityRenderer→texture); native path = roll LBS skinning in Metal
  (GLTFKit2 as parser only). This is a real feature (days→weeks), not a model port.
- Neither turnkey service does true _generated_ motion — it's library retarget. For text-driven
  dance, add Uthana/SayMotion as a humanoid motion stage.

## Flags to verify before committing

Tripo "100+ anims"/dance presets + per-asset non-humanoid rig quality · Meshy quadruped (marketing
says yes, API docs say humanoid-only) · Anything World pricing/commercial-license (contact them) ·
`RealityRenderer` iOS-min badge · HY-Motion/Hunyuan full license text · UniRig Replicate port's
output container.

## Key sources

docs.meshy.ai/en/api/rigging-and-animation · platform.tripo3d.ai/docs/animation ·
github.com/VAST-AI-Research/{UniRig,tripo-python-sdk} · anything-world.gitbook.io/anything-world/api ·
uthana.com/docs/api · fal.ai/models/fal-ai/hunyuan-motion · github.com/warrenm/GLTFKit2 ·
developer.apple.com/documentation/realitykit/realityrenderer · github.com/google/usd_from_gltf
