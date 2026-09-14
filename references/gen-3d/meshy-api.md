---
topic_id: "v2:DGEO"
topic_path: "model-runners/gen-3d-contracts"
semantic_id: "S0CXufxTUgeH0GpkdQtD13E4ZKYIEAAJ"
related_ids:
  - "TsAQGOxT0AeZWDpidQ9rV_FZbqdZEAAB"
  - "Xk0bvdbWEkcN1WJodG5DB2NydLaMMAAO"
---
# Meshy REST API — concrete endpoint contract

The Meshy parallel to `tripo-api.md`: base URL, auth, the text/image-to-3D + rig + animate task
types, the async poll model, and the GLB/PBR outputs — plus where Meshy diverges from Tripo so the
agent can pick. Meshy is the pick for a **humanoid that should DANCE** (biggest motion library,
incl. a Dancing category) and it **accepts an external GLB** so you can generate elsewhere and rig
here.

**Grounded in the official hosted API docs** (`docs.meshy.ai/en/api/*`, read 2026-06-29) — unlike
Tripo's docs these pages render server-side enough for WebFetch to read the request shapes. There
is **no public Python SDK that mirrors the REST surface** the way Tripo's does, so the hosted docs
ARE the primary source here; that makes the SPA-drift risk higher, so **verify live before a real
call** (per CLAUDE.md). Endpoints below were each confirmed from their own doc page (cited in
Sources).

## Base URL + auth

- **Base URL:** `https://api.meshy.ai`.
- **Auth header:** `Authorization: Bearer <MESHY_API_KEY>`.
- **Key location in THIS repo:** `MESHY_API_KEY` env var (gitignored settings). Never hardcode; if
  missing/empty, stop and tell the user to set it and where to get the key. Don't guess a key.

## The one core pattern: POST to create → poll GET → download

Same async shape as Tripo, with three notable contract differences (see "Meshy vs Tripo" below):

1. **Create returns a bare id**, not an envelope: `{"result": "<task-id>"}`.
2. **Status enum is SCREAMING_SNAKE:** `PENDING` · `IN_PROGRESS` · `SUCCEEDED` · `FAILED` ·
   `CANCELED`. (Tripo uses `queued/running/success/failed/...`.)
3. **Endpoints are versioned per-feature:** text-to-3D is under `/openapi/v2/...`; image-to-3D,
   rigging, and animation are under `/openapi/v1/...`. Don't assume one version prefix.

Every create endpoint also has a **`GET /.../{id}/stream`** Server-Sent-Events variant if you'd
rather subscribe than poll. Poll etiquette: the task object carries `progress` (0–100); back off,
don't hammer.

## Generation task types

### `text_to_3d` — `POST /openapi/v2/text-to-3d`

Two-phase: a **preview** task (geometry) then an optional **refine** task (texture), keyed off the
preview id.

- **Preview:** `mode:"preview"` (req) · `prompt` (req, ≤600 chars) · `ai_model`
  (`meshy-5`|`meshy-6`|`latest`, def `latest`) · `model_type` (`standard`|`lowpoly`) ·
  `topology` (`quad`|`triangle`, def `triangle`) · `target_polycount` (100–300000, def 30000) ·
  `pose_mode` (`a-pose`|`t-pose`|`""`) · `should_remesh` · `target_formats`
  (`["glb","obj","fbx","stl","usdz","3mf"]`) · `moderation`.
- **Refine:** `mode:"refine"` (req) · `preview_task_id` (req; preview must be `SUCCEEDED`) ·
  `enable_pbr` (def false — emits metallic/roughness/normal/emission maps) · `hd_texture` (4K base
  color, meshy-6/latest only) · `texture_prompt` · `texture_image_url` · `remove_lighting`
  (def true, meshy-6/latest only) · `target_formats`.
- **Poll:** `GET /openapi/v2/text-to-3d/{id}`.

### `image_to_3d` — `POST /openapi/v1/image-to-3d`

- `image_url` (req; `.jpg/.jpeg/.png` or base64 data URI) OR `input_task_id` (from a prior
  text-to-image task) · `ai_model` (def `latest`) · `should_texture` (def true) · `enable_pbr`
  (def false) · `model_type` (`standard`|`lowpoly`) · `topology` · `target_polycount`
  (def 30000) · `target_formats`.
- **Poll:** `GET /openapi/v1/image-to-3d/{id}`.
- Output adds `pre_remeshed_glb` and four-view `thumbnail_urls`.

### Generation output (`model_urls` / `texture_urls`)

- `model_urls`: object keyed by requested format — `glb`, `fbx`, `obj`, `mtl`, `usdz`, `stl`,
  `3mf`. **Request `glb`** for the native runtime contract.
- `texture_urls`: array of `{base_color, metallic, normal, roughness, emission}` (the PBR maps
  appear only when `enable_pbr:true`; `emission` is meshy-6/latest only).
- Plus `id`, `type` (`text-to-3d-preview`/`...-refine`), `status`, `progress`, `consumed_credits`,
  `thumbnail_url`.

## The rig + animate flow (the dancing-humanoid pipeline)

Two chained tasks, referencing the prior by task id (Meshy's analog of Tripo's prerigcheck→rig→
retarget — note Meshy has **no separate pre-rig check call**; it just rejects un-riggable input):

### 1. Rig — `POST /openapi/v1/rigging`

- `input_task_id` OR `model_url` (req, one of). **`model_url` = the external-GLB door**: a textured
  humanoid GLB you generated anywhere (≤300k faces) can be rigged here — this is why Meshy is the
  "generate elsewhere, rig+dance here" option.
- `height_meters` (number, def **1.7**) · `texture_image_url` (optional).
- **Requirements (doc-explicit):** textured **humanoid** only; character must face **+Z** (glTF
  forward); rejects untextured meshes, non-humanoid assets, and unclear limb structure. The
  300k-face limit applies when using `input_task_id`.
- **Poll:** `GET /openapi/v1/rigging/{id}`. Output `result`: `rigged_character_fbx_url`,
  **`rigged_character_glb_url`** (take this), and a `basic_animations` object (default walk/run
  clips, with/without armature). `DELETE /openapi/v1/rigging/{id}` removes a task.

### 2. Animate — `POST /openapi/v1/animations`

- `rig_task_id` (req; a `SUCCEEDED` rigging task) · `action_id` (req, **integer** — selects a clip
  from the library) · `post_process` (optional `{operation_type, fps}`).
- **Poll:** `GET /openapi/v1/animations/{id}`. Output: **`animation_glb_url`** (take this),
  `animation_fbx_url`, `processed_usdz_url`, `processed_armature_fbx_url`,
  `processed_animation_fps_fbx_url`.

### The animation library (and what I could NOT confirm)

The animate doc references an **"Animation Library Reference"** for browsing `action_id` values but
the API-doc excerpt I read **does not enumerate the clips, the category list, or a programmatic
list endpoint** — so I could not verify from a live source the exact count or that a clip literally
labeled "Dancing" exists at a given `action_id`. The vendor-comparison note (`rig-and-animate-apis.md`)
records "~580–700 clips incl. a Dancing category" from the broader 2026-06-28 research; treat the
specific dance clip as a **flag to confirm live** by reading the Animation Library Reference and
grabbing the real `action_id` before promising "it dances."

## Meshy vs Tripo — choosing between them (pipeline deltas)

| Axis                  | Meshy                                                    | Tripo                                                      |
| --------------------- | -------------------------------------------------------- | ---------------------------------------------------------- |
| **Subjects rigged**   | **Humanoid only** (API rejects non-humanoid)             | **Arbitrary** (biped/quad/avian/serpentine/aquatic, auto)  |
| **Dance motion**      | **Yes** — large action library incl. Dancing (verify id) | **No dance preset** (11 humanoid + 5 gait locomotion only) |
| **External-mesh rig** | **Yes** via `model_url` (≤300k faces, textured humanoid) | Yes via `import_model` (STS upload → task graph)           |
| **Create response**   | `{"result":"<id>"}` (bare)                               | `{"code":0,"data":{"task_id":...}}` (envelope, code==0)    |
| **Status enum**       | `PENDING/IN_PROGRESS/SUCCEEDED/FAILED/CANCELED`          | `queued/running/success/failed/cancelled/banned/...`       |
| **Version prefix**    | mixed `/openapi/v2/` (text) + `/openapi/v1/` (rest)      | one `/v2/openapi` base                                     |
| **Pre-rig gate**      | none (rig just rejects bad input)                        | explicit `animate_prerigcheck` → `riggable`/`rig_type`     |
| **Cost (rig/anim)**   | rig **5cr**, anim **3cr** (cheapest)                     | rig ~25cr/$0.25, retarget ~10cr/$0.10                      |

**Decision rule (mirrors the agent remit):** humanoid that should **dance** → Meshy. Anything
**non-humanoid** / "just rig whatever" → Tripo (only REST option that rigs non-humanoids). Want a
mesh from Tripo but a dance on it → generate on Tripo, export GLB, **rig+animate on Meshy via
`model_url`** (humanoid only, must face +Z, textured, ≤300k faces).

## Project fit — what to request for the native iOS runtime

The native consumer (`native-skinning-runtime.md`) wants **GLB, never FBX**, with
`POSITION/TEXCOORD_0/JOINTS_0/WEIGHTS_0`, a single skin, a node tree, a base-color material, and
`animation` channels — **no sparse accessors, no morph targets**. So:

- Always include `"glb"` in `target_formats`; take `rigged_character_glb_url` /
  `animation_glb_url`. Ignore the FBX/USDZ siblings.
- Keep `enable_pbr:false` if you only need base color (the unlit runtime samples
  `base_color` only) — but PBR-on does no harm, the loader just ignores the extra maps.
- Save the downloaded GLB to `ios/KaraokeVR/GenAssets/<name>.glb` (Xcode 16 synced folder
  auto-bundles it — no `.pbxproj` edit). Record provenance (vendor + prompt + task id + `action_id`).

## Licensing + cost (verify live; both matter — ships under the LLC)

- **License by tier:** Free = **CC BY 4.0** (attribution required) · Pro/Studio = full ownership
  ("you own all assets you create with Meshy"). If the key is on the free tier, the asset carries an
  attribution obligation before a shipped/recorded karaoke take. Don't assume the tier — check or
  ask. Full breakdown in `generation-cost-and-licensing.md`.
- **Cost (credits):** text-to-3D preview 5cr (meshy-6/lowpoly 20cr); refine/texture 10cr;
  image-to-3D 5–30cr (model × texture); **rig 5cr; animation 3cr**. `consumed_credits` is on each
  task object. Don't fan out speculative generations.

## Sources

- `docs.meshy.ai/en/api/text-to-3d` — base URL, auth, preview/refine params, `model_urls`/
  `texture_urls`, status enum (read 2026-06-29).
- `docs.meshy.ai/en/api/image-to-3d` — image endpoint + `input_task_id`, outputs (read 2026-06-29).
- `docs.meshy.ai/en/api/rigging-and-animation` and `docs.meshy.ai/en/api/animation` — `/rigging`
  and `/animations` endpoints, params, humanoid-only/+Z requirement, output urls (read 2026-06-29).
- `docs.meshy.ai/en/api/pricing` — per-operation credit costs (read 2026-06-29).
- `meshy.ai/pricing` — tier license wording (CC BY 4.0 free / ownership paid) (read 2026-06-29).
- Companions: `rig-and-animate-apis.md` (vendor decision) · `tripo-api.md` (the Tripo twin) ·
  `native-skinning-runtime.md` (the GLB output contract) · `generation-cost-and-licensing.md`.
- **Could not verify live:** the animation library's exact clip count / category names / the
  `action_id` of a "Dancing" clip (the doc points to an "Animation Library Reference" not in the
  fetched excerpt) — confirm before promising a dance. The dedicated legal/terms pages
  (`docs.meshy.ai/en/legal/*`) 404'd on fetch; license wording above is from `meshy.ai/pricing`.
