# prunaai/hunyuan3d-2

Model page: https://replicate.com/prunaai/hunyuan3d-2

Tencent's **HunYuan 3D v2** image-to-3D model, optimized with the Pruna toolkit for faster inference. Takes a single reference image and produces a **textured 3D mesh** — not just geometry. Output is a `.glb` (default) or `.obj` file, ready to drop into Blender, Three.js, Unity, Unreal, or any glTF-aware viewer.

## Input schema

| Field                 | Type         | Required      | Default              | Description                                                                                                     |
| --------------------- | ------------ | ------------- | -------------------- | --------------------------------------------------------------------------------------------------------------- |
| `image_path`          | string (URI) | ✅ (de facto) | —                    | Input reference image for 3D reconstruction.                                                                    |
| `file_type`           | enum         |               | `"glb"`              | Output format: `glb` (textured, portable) or `obj` (with separate materials).                                   |
| `speed_mode`          | enum         |               | `"Juiced 🔥 (fast)"` | Exactly `"Juiced 🔥 (fast)"` or `"Unsqueezed 🍋 (highest quality)"` — **literal emojis included**.              |
| `face_count`          | integer      |               | `40000`              | Target number of faces after mesh simplification. Drop to 10k–20k for game-engine use, keep 40k+ for rendering. |
| `octree_resolution`   | integer      |               | `200`                | Geometry detail grid. Higher = finer detail, slower.                                                            |
| `num_inference_steps` | integer      |               | `50`                 | Diffusion steps. Lower = faster, less detailed.                                                                 |
| `num_chunks`          | integer      |               | `20000`              | Internal chunking; rarely needs tuning.                                                                         |
| `generator_seed`      | integer      |               | `12345`              | For reproducibility.                                                                                            |

Local image path for `image_path` is auto-uploaded by `run_model.py`.

## Output

A dict with one key:

```json
{ "mesh_paint": "https://replicate.delivery/.../mesh.glb" }
```

`run_model.py` saves it as `prunaai_hunyuan3d-2_mesh_paint.glb` (or `.obj`).

## Pricing and runtime

- **~$0.22 per run**
- **~3 minutes** typical runtime (varies with `num_inference_steps`, `octree_resolution`, and `speed_mode`)
- Runs on Nvidia A100 (80GB)

## Examples

**Minimal (textured glb, fast mode):**

```bash
python scripts/run_model.py prunaai/hunyuan3d-2 \
    --input '{"image_path": "./reference.png"}' \
    --output ./out/
```

**High-quality game-asset target:**

```bash
python scripts/run_model.py prunaai/hunyuan3d-2 \
    --input '{
      "image_path": "./character_turnaround_front.png",
      "speed_mode": "Unsqueezed 🍋 (highest quality)",
      "face_count": 15000,
      "octree_resolution": 256,
      "num_inference_steps": 75,
      "file_type": "glb"
    }' \
    --output ./out/
```

**OBJ with separate materials (for DCC tools that prefer it):**

```bash
python scripts/run_model.py prunaai/hunyuan3d-2 \
    --input '{
      "image_path": "./reference.png",
      "file_type": "obj",
      "face_count": 30000
    }' \
    --output ./out/
```

## Good reference images

- Clean background (white or neutral). The model infers geometry partly from silhouette — busy backgrounds confuse it.
- Full subject visible (head-to-toe for characters, whole object for props).
- Orthographic-ish or slight 3/4 angle beats extreme perspective. Pure side or front views can collapse depth cues.
- Reasonable resolution (512px+ on the short side).

## Tuning notes

- **`speed_mode`** — literal string with emoji. Copy-paste exactly: `"Juiced 🔥 (fast)"` or `"Unsqueezed 🍋 (highest quality)"`. JSON must be UTF-8 (it is by default).
- **`face_count`** — simplification target applied post-reconstruction. Good presets:
  - Background/hero props: 40k–80k
  - Rigged characters for games: 10k–20k
  - Web/AR (gltf-loader): 5k–15k
- **`octree_resolution`** — 200 is a reasonable default. Bumping to 256–300 catches finer detail at noticeable runtime cost.
- **`num_inference_steps`** — diminishing returns past ~75. Default 50 is fine for most images.

## Gotchas

- The two `speed_mode` enum values include emoji characters verbatim — a plain `"fast"` won't work. If you get a 422 validation error, check the string exactly.
- Output is geometry + baked texture — **no separate PBR maps** (normal, roughness, metallic). For PBR-ready assets, bake or extract from the glb downstream in Blender.
- Single-view reconstruction has inherent ambiguity on unseen sides. For hero assets, the typical workflow is to generate, then manually clean up the back/underside in a DCC.
- Transparent PNGs work but subjects on solid backgrounds often reconstruct cleaner.
