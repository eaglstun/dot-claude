# Per-model deep-dive index

Each entry below corresponds to a file in `references/models/<slug>.md` covering unusual schemas, pricing, and gotchas for that model. When the user's request matches a model listed here, read that file first.

For picking _which_ model to use within a modality (decision tables + quick picks), use the category selection files in `references/` (`image-models.md`, `video-models.md`, `audio-models.md`, `segmentation-models.md`) instead of this index.

## Image — generation

- `andreasjansson/illusion` — optical-illusion image gen: hides a QR code / logo pattern inside a prompt-guided scene; ~$0.0033/run on L40S
- `black-forest-labs/flux-dev-lora` — Flux Dev with up to 2 stackable LoRAs (Replicate/HF/Civitai/any .safetensors URL)
- `bria/fibo` — 8B text-to-image trained on 100% licensed data; structured JSON prompting (lighting/camera/composition) + Generate/Refine/Inspire modes for rights-clear enterprise use
- `bria/image-3.2` — Bria's standard text-to-image on 100% licensed data; simpler than FIBO (prompt-only, no structured-prompt/modes), same aspect-ratio tooling
- `bytedance/bagel` — unified multimodal: T2I, image editing, and visual Q&A in one endpoint via `task` enum; outputs `{text, image}`; ~$0.096/run, ~99s
- `fofr/latent-consistency-model` — LCM: 4–8-step SD for ~10× speed; low CFG (1–2, not 7); ~$0.039/run, sub-$0.001/image with `num_images` batches
- `lucataco/flux-dev-multi-lora` — Flux Dev with up to 20 stacked LoRAs (array inputs, cheap ~$0.029/run)
- `lucataco/realistic-vision-v5.1` — popular photoreal SD 1.5 fine-tune; very cheap (~$0.001–0.003/run), strong portraits, SD 1.5-era resolution ceiling

## Image — editing / composition

- `adirik/interior-design` — restyle interior-room photos via prompt (MLSD + seg ControlNet on Realistic Vision, preserves walls/windows/doorways); ~$0.0076/run
- `afterpeak/flux-slowed` — Flux LoRA for "slowed-audio YouTube/TikTok cover art" aesthetic (female-portrait bias, soft-lit, polished); trigger `SLOW3D`; author default `lora_scale: 0.8`; ~$0.045/run
- `aramintak/flux-film-foto` — Flux LoRA for neutral 35mm / medium-format film look (grain, halation, print texture); trigger `flmft photo style`; ~$0.014/run on H100, ~10s typical
- `black-forest-labs/flux-canny-pro` — Flux Pro with Canny-edge ControlNet (~$0.05/img); preserves source line-art, restyle via prompt
- `fermatresearch/magic-image-refiner` — SD 1.5 img2img refiner with creativity/resemblance/hdr sliders + mask (doubles as inpainter), ~$0.05/run
- `flux-kontext-apps/multi-image-kontext-max` — BFL Flux Kontext Max: 2-image prompt-driven composition/edit (`input_image_1` + `input_image_2` both required); ~$0.08/img
- `fofr/face-swap-with-ideogram` — generative "face-swap" (Ideogram character-ref re-renders target with a person's identity; not pixel-level grafting)
- `fofr/flux-bad-70s-food` — Flux LoRA meme: unappetizing 1970s cookbook-photo aesthetic (gelatin salads, beige casseroles); trigger `bad 70s food` (likely); hits hard at default `lora_scale: 1.0`; ~$0.018/run
- `fofr/kontext-ps1` — Flux Kontext fine-tune for PS1/early-3D aesthetic (low-poly, dithered, texture warping); prompt nudgeable but style hardcoded; $0.036/run on H100
- `jagilley/controlnet-scribble` — original 2023 ControlNet-scribble on SD 1.5: doodle + prompt → image; cheap, fast iteration
- `levelsio/lomography` — Flux LoRA for analog Lomo film aesthetic (saturated color, vignette, light leaks); trigger word `TOK lomography`; `lora_scale` as main strength knob; $0.029/run

## Image — restoration / upscaling

- `cswry/seesr` — semantic-aware diffusion super-resolution; text/tag prompt guides the upscale; handles severely-degraded inputs
- `fofr/kontext-fix-jpeg-compression` — Flux Kontext fine-tune targeting JPEG compression artifacts (same-resolution cleanup, not upscale); steerable prompt ("preserve film grain"); $0.10/run on H100
- `recraft-ai/recraft-creative-upscale` — Recraft's **creative** upscaler: hallucinates detail (opposite end from Topaz on fidelity/creativity axis); single-input schema, no knobs, WebP output
- `recraft-ai/recraft-crisp-upscale` — Recraft's **crisp** upscaler: faithful, sharpen/clean, doesn't hallucinate; identical 1-input schema to creative-upscale, ~5× faster (~9s vs ~47s)
- `sczhou/codeformer` — blind face restoration via transformer codebook; tunable fidelity↔identity slider; one of the cheapest image models on Replicate (~$0.004/run)
- `tencentarc/gfpgan` — classic blind face restoration (Tencent ARC); `version` enum v1.2/v1.3/v1.4/RestoreFormer; very cheap (~$0.0027/run), softer than CodeFormer
- `topazlabs/image-upscale` — commercial-grade image upscaler (up to 6× / 512 MP) with 5 model variants + face enhancement

## Video — generation

- `bytedance/seedance-2.0` — ByteDance's flagship T2V + I2V + reference modes; native audio on by default, up to 15s, 8 aspect ratios (incl. 21:9 / 9:21 / adaptive); strong default pick for general T2V
- `kwaivgi/kling-v3-omni-video` — unified Kling 3.0: text/image/reference-based video gen + video editing, multi-shot, native audio
- `lightricks/ltx-video` — fast open-source T2V/I2V (up to 257 frames ≈ 10.7s @ 24fps); ~$0.08/run on L40S
- `minimax/video-01-director` — Minimax T2V/I2V with in-prompt camera tags (`[Push in]`, `[Pan left]`, …); 15 tags, combine 3/group; 720p 6s
- `pixverse/pixverse-v5` — predecessor to v6; only reason to pick it is the 15-value `effect` enum (Let's YMCA!, Ghibli Live!, Kungfu Club, etc.) — v6 dropped that field. Otherwise use v6.
- `pixverse/pixverse-v6` — cheap/fast text+image-to-video; adds camera control, POV, multi-shot; tiered per-second pricing ($0.05–$0.23/s by resolution+audio)
- `prunaai/p-video` — fast, cheap text/image/audio-to-video with a draft mode (~$0.005/s at 720p)
- `runwayml/gen-4.5` — premium text-to-video / image-to-video (#1 on AA benchmark; 5s or 10s, 6 aspect ratios)
- `vidu/q3-pro` — text/image/start-end video generation, up to 16s @ 1080p, with audio
- `wan-video/wan-2.7-i2v` — image-to-video + first-last-frame + clip continuation + audio-sync, up to 15s @ 1080p

## Video — editing / motion / lipsync / matting / colorization

- `arielreplicate/deoldify_video` — colorizes B&W video via DeOldify (render_factor-tunable); ~$0.11/run on T4, ~8 min typical
- `arielreplicate/robust_video_matting` — human video matting / background removal (green-screen, alpha, or RGBA foreground)
- `bytedance/dreamactor-m2.0` — motion/expression transfer: image + driving video → animated character (humans, cartoons, animals)
- `heygen/lipsync-speed` — audio-driven lipsync (video + audio → lipsynced video)
- `wan-video/wan-2.7-videoedit` — prompt-driven editing of an existing video (background swap, style, lighting, outfit)
- `zsxkib/multitalk` — image + up to two audio tracks → conversational two-person lipsynced video
- `zsxkib/stable-video-face-restoration` — video-domain face restoration with temporal stability (video-diffusion backbone + face prior); ~2s/frame on L40S, single front-facing subject best

## Segmentation

- `cjwbw/semantic-segment-anything` — automatic dense segmentation + per-mask semantic labels (SAM + classifier); no prompt needed, dict output (labeled PNG + JSON)
- `meta/sam-2` — Meta's official SAM 2 (image-only, "segment everything" auto-mode); combined mask + array of per-object masks, ~$0.011/run
- `schananas/grounded_sam` — text-prompt segmentation ("cat, dog" → masks); thin wrapper (4 inputs), returns annotated + raw mask + inverted mask

## Audio — music / SFX generation

- `stability-ai/stable-audio-2.5` — text-to-music / text-to-SFX, 1–190s stereo MP3 output; prompt-only (no audio-conditioning exposed on Replicate despite marketing); instrumental, no lyrics

## Audio — TTS

- `lucataco/orpheus-3b-0.1-ft` — Canopy Labs' Orpheus 3B (Llama-based) TTS; 4 preset voices (tara/dan/josh/emma) + 9 emotion tags (`<laugh>`, `<sigh>`, `<cough>`, …); no 13s cap, ~$0.075/run on L40S. Recommended default for expressive English TTS.
- `resemble-ai/chatterbox` — open-source expressive TTS with zero-shot voice cloning (`audio_prompt`) + `exaggeration` emotion slider (0.25–2)
- `suno-ai/bark` — Suno's expressive text-to-audio: 131 voice presets × 13 languages, nonverbal tags (`[laughter]`, `[music]`); ~$0.04/run, ~13s cap per gen

## Audio — speech-to-text / transcription

- `sabuhigr/sabuhi-model` — Whisper large-v2 + pyannote diarization (hard cap 1–2 speakers); requires user-supplied HF token; ~$0.055/run. Single-author 2023 wrapper — prefer WhisperX-based alternatives for new work.

## Audio — voice cloning / conversion

- `lucataco/singing_voice_conversion` — Amphion DiffWaveNetSVC (not RVC); 15 preset target singers + pitch/key controls; ~$0.11/run
- `zsxkib/realistic-voice-cloning` — RVC voice cloning with 10 preset voices (Drake, Vader, Obama…) + CUSTOM `.zip` URL; ~$0.033/run

## Audio — RVC pipeline / pitch correction

- `nateraw/autotune` — classic pitch-correction autotune (PSOLA + pyin); `scale` enum of 25 (closest / major / minor); CPU-only, ~$0.007/run
- `replicate/train-rvc-model` — RVC voice-conversion _trainer_ (zip of WAV chunks → trained voice model)
- `zsxkib/create-rvc-dataset` — RVC dataset builder: YouTube URL → zip of vocal-separated, chunked .mp3 clips ready for `replicate/train-rvc-model`; ~$0.054/run

## 3D

- `prunaai/hunyuan3d-2` — image-to-3D textured mesh (glb/obj), ~3min, ~$0.22/run
