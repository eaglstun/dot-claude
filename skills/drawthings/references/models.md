# Draw Things — installed models (running inventory)

A living list of what's installed in the local Draw Things app. **Last refreshed:
2026-06-01.** Append new entries as models are added.

The API has **no endpoint to enumerate models** (`/sdapi/v1/sd-models` etc. return
empty in Draw Things). The source of truth is the on-disk model folder:

```text
~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models/
```

Human-readable names ↔ filenames live in that folder's `custom.json`,
`custom_lora.json`, `custom_controlnet.json`, and `custom_textual_inversions.json`.
To pass a model over the API, use the **filename** in the `model` field (e.g.
`"model": "flux_1_dev_q8p.ckpt"`). To refresh this list:

```bash
ls -S "$HOME/Library/Containers/com.liuliu.draw-things/Data/Documents/Models"/*.ckpt
```

> Quant suffixes: `q8p`/`q6p`/`q5p` = 8/6/5-bit palettized, `f16`/`f32` = full
> precision. Lower bits = smaller/faster, slightly lower fidelity.

---

## Base image models (selectable as `model`)

### FLUX.1

| Model                               | File                                       | Notes                                                                                                 |
| ----------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| FLUX.1 [dev] (8-bit)                | `flux_1_dev_q8p.ckpt`                      | **Default loaded.** guidance_scale ~3.5, 12–20 steps. Pair with FLUX.1 Turbo Alpha LoRA for few-step. |
| FuxCapacity (FLUX, adult)           | `fuxcapacitynsfwporn_62bf16_f16.ckpt`      | 22 GB full-precision FLUX finetune                                                                    |
| Gonzalo MOXL Flux/Pony v3.0 (adult) | `gonzalomoxlfluxpony_v30fluxdaio_f16.ckpt` | 22 GB FLUX/Pony hybrid finetune                                                                       |

### Qwen-Image

| Model                        | File                            | Notes                            |
| ---------------------------- | ------------------------------- | -------------------------------- |
| Qwen-Image-Edit 2509 (8-bit) | `qwen_image_edit_2509_q8p.ckpt` | Instruction-driven image editing |

### Z-Image

| Model                     | File                         | Notes                       |
| ------------------------- | ---------------------------- | --------------------------- |
| Z-Image Turbo 1.0 (8-bit) | `z_image_turbo_1.0_q8p.ckpt` | Fast / few-step turbo model |

### SDXL

| Model                         | File                                     | Notes                       |
| ----------------------------- | ---------------------------------------- | --------------------------- |
| SDXL Base 1.0                 | `sd_xl_base_1.0_f16.ckpt`                |                             |
| SDXL Refiner 1.0              | `sd_xl_refiner_1.0_f16.ckpt`             | refiner stage for SDXL base |
| Juggernaut XL v9              | `juggernaut_xl_v9_f16.ckpt`              |                             |
| RealVisXL v4.0                | `realvisxl_v4.0_f16.ckpt`                | photoreal                   |
| Jib-Mix-Realistic-XL          | `jib_mix_realistic_xl_f16.ckpt`          | photoreal                   |
| Pony Realism v2.2             | `pony_realism_v2.2_914390_f16.ckpt`      | Pony-based                  |
| realismByStableYogi PonyV3VAE | `realismbystableyogi_ponyv3vae_f16.ckpt` | Pony-based                  |

### SD 1.5 / 2.x

| Model                    | File                                               | Notes            |
| ------------------------ | -------------------------------------------------- | ---------------- |
| SD 1.5                   | `sd_v1.5_f16.ckpt`                                 |                  |
| SD 1.5 Inpainting        | `sd_v1.5_inpainting_f16.ckpt`                      |                  |
| SD 2.1                   | `sd_v2.1_f16.ckpt`                                 |                  |
| SD 2.0 Inpainting        | `sd_v2.0_inpainting_f16.ckpt`                      |                  |
| Realistic Vision v5.1    | `realistic_vision_v5.1_f16.ckpt`                   |                  |
| Realistic Vision v6.0 B1 | `sg161222_realistic_vision_v6.0_b1_novae_f16.ckpt` | no-VAE build     |
| Openjourney (mdjrny v4)  | `mdjrny_v4_f16.ckpt`                               | MidJourney-style |
| Analog Diffusion         | `wavymulder_analog_diffusion_f16.ckpt`             | film look        |

### PixArt

| Model              | File                                 | Notes |
| ------------------ | ------------------------------------ | ----- |
| PixArt-Σ XL 2 1024 | `pixart_sigma_xl_2_1024_ms_f16.ckpt` |       |

## Video models

| Model                                      | File                             | Notes                                     |
| ------------------------------------------ | -------------------------------- | ----------------------------------------- |
| Wan 2.2 A14B High-Noise Expert T2V (8-bit) | `wan_v2.2_a14b_hne_t2v_q8p.ckpt` | text→video; pair with Wan Lightning LoRAs |
| Wan 2.2 5B TI2V (8-bit)                    | `wan_v2.2_5b_ti2v_q8p.ckpt`      | text/image→video                          |

## ControlNets & adapters

| Name                                 | File                                                           | For                                            |
| ------------------------------------ | -------------------------------------------------------------- | ---------------------------------------------- |
| Union Pro 2.0 (5-bit)                | `controlnet_union_pro_flux_1_dev_2.0_q5p.ckpt`                 | FLUX.1 — multi-type control                    |
| Alimama Inpaint Beta                 | `controlnet_alimama_inpaint_flux_1_dev_beta_q8p.ckpt`          | FLUX.1 — inpainting                            |
| PuLID 0.9.1                          | `pulid_0.9.1_eva02_clip_l14_336_f16.ckpt`                      | FLUX.1 — **identity/face** (needs a ref image) |
| FLUX.1 Redux                         | `flux_1_redux_f16.ckpt`                                        | FLUX.1 — image-variation / vision conditioning |
| Pose (Kwai Kolors)                   | `controlnet_pose_kwai_kolors_1.0_q6p_q8p.ckpt`                 | Kolors — pose                                  |
| IP-Adapter FaceID Plus (Kwai Kolors) | `ip_adapter_faceid_plus_kwai_kolors_1.0_clip_l14_336_q8p.ckpt` | Kolors — face id                               |
| OpenPose 2.x                         | `controlnet_openpose_2.x_f16.ckpt`                             | SD 1.x/2.x — pose                              |
| Depth 1.x v1.1                       | `controlnet_depth_1.x_v1.1_f16.ckpt`                           | SD 1.x/2.x — depth                             |

## Upscalers & restoration

| Name               | File                          |
| ------------------ | ----------------------------- |
| RealESRGAN x4plus  | `realesrgan_x4plus_f16.ckpt`  |
| RestoreFormer v1.0 | `restoreformer_v1.0_f16.ckpt` |
| ParseNet v1.0      | `parsenet_v1.0_f16.ckpt`      |

## LoRAs

17 LoRA files are on disk. `custom_lora.json` was pruned on 2026-06-01 to the 13 entries
whose files exist (orphaned registry entries removed; backup at
`custom_lora.json.bak-20260601`).

**Speed / distillation:** FLUX.1 Turbo Alpha (`flux.1_turbo_alpha_lora_f16.ckpt`),
SDXL Lightning 4-Step (`sdxl_lightning_4_step_lora_f16.ckpt`), LCM — SDXL base/refiner &
SD 1.5 (`lcm_sd_xl_base_1.0`, `lcm_sd_xl_refiner_1.0`, `lcm_sd_v1.5` `_lora_f16.ckpt`),
TCD — SDXL & SD 1.5 (`tcd_sd_xl_base_1.0`, `tcd_sd_v1.5` `_lora_f16.ckpt`), Wan 2.2
Lightning High/Low-Noise Expert T2V (`wan_v2.2_a14b_{hne,lne}_t2v_lightning_v2.0_lora_f16.ckpt`).

**Style / quality:** Amateur Photography v3.5 [dev] (`amateur_photography_v3.5__dev__lora_f16.ckpt`),
Analog Diffusion v1.0 (`analog_diffusion_v1_lora_f16.ckpt`), Openjourney v1.0
(`openjourney_v1_lora_f16.ckpt`), add-detail-xl (`add_detail_xl_lora_f16.ckpt`),
SDXL offset (`sdxl_offset_v1.0_lora_f16.ckpt`), In-Context Portrait Photography
(`in_context__portrait_photography_lora_f16.ckpt`), AmateurStyle v1 Pony Realism
(`amateurstyle_v1_pony_realism_lora_f16.ckpt`).

**Other:** `ericoo_2000_lora_f32.ckpt` (a 2000-step custom training run). The kept
`custom_lora.json` also includes two ~4 KB companion stubs for the FuxCapacity / Gonzalo
base finetunes.

## Support files (NOT selectable as generation models)

Text encoders, vision/caption models, and VAEs that other models depend on — listed for
completeness so they aren't mistaken for base models:

- **Text encoders:** `t5_xxl_encoder_q6p`, `umt5_xxl_encoder_q8p`, `clip_vit_l14*`,
  `open_clip_vit_bigg14`, `open_clip_vit_h14`, `siglip_*`, `eva02_clip_l14_336`,
  plus per-model `*_clip_vit_l14` / `*_open_clip_vit_bigg14` companions.
- **VAEs:** `flux_1_vae`, `sdxl_vae_v1.0`, `vae_ft_mse_840000`, `qwen_image_vae`,
  `wan_v2.1_video_vae`, `wan_v2.2_video_vae`.
- **Caption / vision-language (for interrogate / image→text):** `qwen_2.5_vl_7b`,
  `qwen_3_vl_4b_instruct`, `moondream1`/`moondream2`, `blip2_*`, `opt_2.7b`.
- **Other:** `depth_anything_v2.0` (depth maps), `arcface` (face embeddings for PuLID/FaceID).

## Registered-but-not-downloaded

These appear in `custom.json` (the app's model list) but their weight files are not on
disk — they'd re-download on selection: Ghibli v1, epiCRealism, AnalogMadness v7,
DreamShaper XL v2.1 Turbo, Stable Cascade (Würstchen v3.0). Partial/interrupted
downloads also present: Qwen-Image 1.0, Qwen-Image-Edit 2509 q6p, HunyuanVideo T2V 720p,
SVD i2v XT 1.1.
