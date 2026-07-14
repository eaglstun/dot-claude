---
topic_id: "v2:DGEB"
topic_path: "model-runners/gen-3d-contracts"
semantic_id: "TsAQGOxT0AeZWDpidQ9rV_FZbqdZEAAB"
related_ids:
  - "S0CXufxTUgeH0GpkdQtD13E4ZKYIEAAJ"
  - "Xk0bvdbWEkcN1WJodG5DB2NydLaMMAAO"
---
# Tripo3D REST API — concrete endpoint contract

The HOW-TO-CALL companion to `rig-and-animate-apis.md` (which is the WHY — the vendor decision).
This is the actual REST surface: base URL, auth, every task type, the poll loop, and the rig→
animate flow for the karaoke pipeline.

**Grounded in the official SDK** (`github.com/VAST-AI-Research/tripo-python-sdk`, branch `master`,
read 2026-06-28) — the SDK is a thin wrapper over the raw REST `/task` endpoint, so its method
signatures ARE the request schema (every `client.X(...)` just POSTs a `{"type": ...}` body). The
hosted docs (`platform.tripo3d.ai/docs`) are a JS SPA that WebFetch can't read; the SDK source is
the reliable mirror. **Still verify live before a real call** — these APIs drift (per CLAUDE.md).

## Base URL + auth

- **Base URL:** `https://api.tripo3d.ai/v2/openapi` (global). Non-global/China twin:
  `https://api.tripo3d.com/v2/openapi`.
- **Auth header:** `Authorization: Bearer <TRIPO_API_KEY>`.
- **Key format:** must start with `tsk_` (the SDK rejects anything else before sending).
- **Key location in THIS repo:** `TRIPO_API_KEY` lives in `.claude/settings.local.json` env
  (gitignored). Never hardcode; if missing, stop and tell the user to set it. See the
  `tripo-api-key-location` memory.

## The one core pattern: POST /task → poll GET /task/{id}

**Everything is a task.** You POST a body whose `type` selects the operation; you get a `task_id`;
you poll until terminal. Chained ops (rig, retarget, texture, convert) reference a prior task by
`original_model_task_id` — you pass the _task id_, not a file.

| Method | Path                | Purpose                                                                             |
| ------ | ------------------- | ----------------------------------------------------------------------------------- | ----- | ----- | ------- |
| `POST` | `/task`             | Create any task. Body `{"type": ..., ...}`. Returns `{"data": {"task_id": "..."}}`. |
| `GET`  | `/task/{task_id}`   | Poll status / fetch result URLs.                                                    |
| `GET`  | `/user/balance`     | `{"data": {"balance": float, "frozen": float}}` (credits).                          |
| `POST` | `/upload/sts/token` | Get STS creds to S3-upload a local file (body `{"format": "jpeg"                    | "png" | "glb" | ...}`). |

**Response envelope (every endpoint):** success is `{"code": 0, "data": {...}}` — `code` is
**always 0 on success**. Errors return HTTP ≥400 with `{"code": <int>, "message": str,
"suggestion": str?}`.

**Create a task (curl):**

```bash
curl -s https://api.tripo3d.ai/v2/openapi/task \
  -H "Authorization: Bearer $TRIPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"text_to_model","prompt":"a chrome disco ball","model_version":"v3.1-20260211"}'
# -> {"code":0,"data":{"task_id":"...uuid..."}}
```

**Poll it:**

```bash
curl -s https://api.tripo3d.ai/v2/openapi/task/<task_id> \
  -H "Authorization: Bearer $TRIPO_API_KEY"
```

### Poll result shape (`data` of GET /task/{id})

```jsonc
{
  "task_id": "...", "type": "text_to_model",
  "status": "running",          // see status enum below
  "progress": 42,               // 0–100
  "running_left_time": 18,      // est. seconds remaining (when running)
  "queuing_num": 0,
  "input": { ... },             // echo of your request
  "output": {                   // populated on success
    "model": "https://...glb?...",      // <- the GLB you want (expiring signed URL)
    "base_model": "https://...",
    "pbr_model": "https://...",
    "rendered_image": "https://....jpg",
    "riggable": true,                    // only on animate_prerigcheck
    "rig_type": "biped"                  // only on animate_prerigcheck
  },
  "error_code": 0, "error_msg": null,
  "create_time": 1719600000
}
```

**Status enum:** `queued` · `running` · `success` · `failed` · `cancelled` · `banned` ·
`expired` · `unknown`. Terminal = {success, failed, cancelled, banned, expired}.
**Output URLs are signed and expire (~24h)** — download promptly, don't store the URL.

**Polling etiquette** (mirror the SDK's `wait_for_task`): start ~2s; if `running_left_time` is
present use ~0.5× it as the next interval; else exponential backoff capped at 30s. Don't hammer.

## Generation task types (the `type` field)

All share a large optional param set; only the type-specific keys differ. Defaults below are the
SDK defaults.

**`text_to_model`** — `prompt` (req, ≤1024 chars) · `negative_prompt` · `model_version`
(default `v2.5-20250123`) · `face_limit` · `texture` (def true) · `pbr` (def true) ·
`texture_quality`/`geometry_quality` (`standard`|`detailed`) · `quad` (def false) · `auto_size` ·
`smart_low_poly` · `generate_parts` · `export_uv` (def true) · `image_seed`/`model_seed`/
`texture_seed` · `compress` (SDK sends the string `"geometry"` when true).

**`image_to_model`** — `file` (req; see file-input below) + all of the above (no `image_seed`),
plus `texture_alignment` (`original_image`|`geometry`) · `orientation` (`default`|`align_image`) ·
`enable_image_autofix`.

**`multiview_to_model`** — `files` (req; array of file-input objects, front/back/left/right) +
same optionals as image. (Note `model_version` list excludes the Turbo build.)

**`import_model`** — bring an EXTERNAL mesh into the task graph so you can rig/texture/convert it.
Upload a local `GLB/OBJ/FBX/STL` via STS, then `{"type":"import_model","file":{...}}`. Returns a
task id usable as `original_model_task_id` downstream. (This is how you'd rig an
`assets/threejs`-style mesh, not just a Tripo-generated one.)

**Mesh-refine family** (all take `original_model_task_id`): `refine_model` · `texture_model` ·
`convert_model` · `stylize_model` (`lego`/`voxel`/`voronoi`/`minecraft`) · `mesh_segmentation` ·
`mesh_completion` · `highpoly_to_lowpoly` (a.k.a. smart lowpoly).

**`model_version` values** (text/image): `P1-20260311` · `Turbo-v1.0-20250506` ·
`v3.1-20260211` · `v3.0-20250812` · `v2.5-20250123` (SDK default) · `v2.0-20240919` ·
`v1.4-20240625`. Newer ≠ always better for this use; pick deliberately.

### File inputs

A `file`/`files`/image param becomes a JSON object, one of:

- `{"type":"jpg","url":"https://..."}` — public URL (simplest; no upload).
- `{"type":"jpg","file_token":"<uuid>"}` — token from a prior legacy upload.
- `{"type":"glb","object":{"bucket":...,"key":...}}` — after STS upload to S3 (preferred for
  local files; needs `boto3`). For local files, the SDK's `upload_file` does STS → falls back to
  legacy token upload if `boto3` is absent.

## The rig + animate flow (what the karaoke character pipeline needs)

Three chained tasks, each referencing the previous by task id:

**1. Pre-rig check** — `{"type":"animate_prerigcheck","original_model_task_id":"<gen_id>"}`.
Result `output.riggable` (bool) + `output.rig_type` (auto-detected). Gate on `riggable==true`.

**2. Rig** — `{"type":"animate_rig","original_model_task_id":"<gen_id>", ...}`:

- `rig_type` — `biped` (def) · `quadruped` · `hexapod` · `octopod` · `avian` · `serpentine` ·
  `aquatic` · `others`. Omit to use the auto-detected type from step 1.
- `spec` — `tripo` (def) · `mixamo`. **Use `tripo` if you will retarget Tripo PRESET clips** —
  `spec=mixamo` is **incompatible with the preset library** and fails retarget with **`error
1004`** (reproduced 3× on 2026-06-28; the presets are authored against Tripo's native skeleton).
  Only choose `mixamo` when you're bringing your OWN Mixamo-authored clips, not Tripo presets. The
  native LBS loader keys off node indices + inverseBind, **not joint names**, so Tripo-native bone
  names (`Root, Hip, Pelvis, L_Thigh, …`) are loader-safe — there's no real upside to mixamo here.
- `out_format` — `glb` (def) · `fbx`. **Use `glb`** (see runtime note).
- `model_version` — `v1.0-20240301` (def) · `v2.0-20250506`.
  Result `output.model` = rigged GLB (skeleton + skin weights, no clip).

**3. Retarget animation** — `{"type":"animate_retarget","original_model_task_id":"<rig_id>",
"animation":"preset:walk", ...}`:

- `animation` — single preset string, OR `"animations":[...]` for multiple (SDK swaps the key when
  you pass a list).
- `out_format` `glb`(def)/`fbx` · `bake_animation` (def true) · `export_with_geometry` (def
  false — set **true** if you want the clip baked into a self-contained GLB rather than a
  skeleton-only delta) · `animate_in_place` (def false — strips root motion; good for a figure
  that should dance in one spot).
  Result `output.model` = animated GLB.

### Animation presets — the full list (and the dance gap)

From the SDK `Animation` enum, the ONLY retarget presets are:

```
preset:idle  preset:walk  preset:run   preset:dive  preset:climb  preset:jump
preset:slash preset:shoot preset:hurt  preset:fall  preset:turn
preset:quadruped:walk  preset:hexapod:walk  preset:octopod:walk
preset:serpentine:march  preset:aquatic:march
```

**There is NO dance preset.** This resolves the open flag in `rig-and-animate-apis.md`
("~16 presets; no clear dance"): confirmed — it's 11 humanoid locomotion/combat clips + 5
non-humanoid gaits, and **none is a dance**. For a _dancing_ karaoke figure, Tripo retarget alone
won't do it: either go **Meshy** (has a Dancing category, humanoid-only) or add a text-to-motion
stage (Uthana / SayMotion) and retarget that clip — don't pass off `preset:jump` as "dancing."

## Conversion (`convert_model`) — note for the GLB runtime

`{"type":"convert_model","original_model_task_id":"<id>","format":"GLTF"}`. Formats: `GLTF` ·
`USDZ` · `FBX` · `OBJ` · `STL` · `3MF`. Key opts: `with_animation` (def true — keep for animated
rigs) · `fbx_preset` (`blender`/`mixamo`/`3dsmax`) · `texture_size` (def 4096) · `texture_format`
(def `JPEG`) · `quad` · `face_limit` · `pivot_to_center_bottom` · `animate_in_place`.

### Decimation — decimate BEFORE rigging, and not with `convert_model face_limit`

To ship a low-poly twin (phone GPU), decimate the mesh and rig the LOW-poly result so the animated
GLB is light. Two field-tested findings (2026-06-28, the dino asset):

- **`convert_model` + `face_limit` is too blunt for thin features** — at `face_limit:5000` it
  collapsed the dino's small arms, and the pre-rig check then returned `riggable:false,
rig_type:others`. **`highpoly_to_lowpoly` (smart lowpoly)** at a higher cap (~8000) preserved the
  limbs and stayed `biped`-riggable. Prefer smart-lowpoly for anything you intend to rig.
- **Order:** generate (full) → `highpoly_to_lowpoly` → `animate_prerigcheck` on the LOW-poly →
  rig → retarget. Always re-run the pre-rig check on the decimated mesh; decimation can destroy
  riggability that the full mesh had.
- `animate_in_place:true` on retarget strips root motion — use it for a fixed stage prop so a
  walk/locomotion clip doesn't drift the model off its placement.

## Project fit — what to request for the native iOS runtime

The native consumer (`native-skinning-runtime.md`) wants **GLB, never FBX**, with
`POSITION/TEXCOORD_0/JOINTS_0/WEIGHTS_0`, a single `skin`, a node tree, a base-color material, and
`animation` channels — **no sparse accessors, no morph targets**. So:

- Always `out_format:"glb"` on rig + retarget; `format:"GLTF"` if you ever convert.
- `spec:"mixamo"` on rig → predictable joint names for the loader.
- `export_with_geometry:true` on retarget → a self-contained animated GLB (mesh + skin + clip in
  one file), which is what a from-scratch loader wants.
- Save the downloaded GLB to `ios/KaraokeVR/GenAssets/<name>.glb` (Xcode 16 synced folder
  auto-bundles it — no `.pbxproj` edit). Record provenance (vendor + prompt + task id).

## Cost + licensing (verify live; both matter — ships under the LLC)

- **Balance** is in credits; check `GET /user/balance` before a batch. Anchors from the research
  (confirm live): rig ~25cr/$0.25, retarget ~10cr/$0.10; generation varies by `model_version`.
- **License by tier:** free = **CC BY 4.0** (attribution required) · Pro/Max = private +
  commercial. If the key is on a free tier, the asset carries an attribution obligation before it
  goes into a shipped/recorded karaoke take. Don't assume the tier — check or ask.

## Error handling

HTTP ≥400 → `{"code","message","suggestion?}`. Common: bad/missing key (key must be `tsk_`),
insufficient balance, unriggable mesh (check step 1 first), expired download URL (re-poll the task
for a fresh signed URL). Surface `message` + `suggestion` verbatim; don't silently retry a
4xx with the same body.

## Sources

- `github.com/VAST-AI-Research/tripo-python-sdk` @ `master` — `tripo3d/client.py` (every task
  type + params/defaults), `tripo3d/models.py` (Animation/RigType/RigSpec/TaskStatus enums, Task/
  Balance shapes), `tripo3d/client_impl/aiohttp_client_impl.py` (auth header, error envelope),
  `examples/{rig_model,retarget_animation,text_to_model,image_to_model}.py`.
- `platform.tripo3d.ai/docs` (general · generation · animation · schema · quick-start) — hosted
  reference; SPA, read it in a browser. Base URL + `model_version` list cross-checked here.
- Companion: `.claude/references/gen-3d/rig-and-animate-apis.md` (vendor decision) ·
  `native-skinning-runtime.md` (the GLB output contract this must satisfy).
