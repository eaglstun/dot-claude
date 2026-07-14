# draw-things-cli — headless inference & LoRA training

`draw-things-cli` (Homebrew: `brew tap drawthingsai/draw-things && brew install
draw-things-cli`) is the **native engine as a command-line tool** — runs with the app
**closed**, uses the same models dir
(`~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models`, or
`$DRAWTHINGS_MODELS_DIR` / `--models-dir`), MPS-accelerated. Subcommands: `generate`,
`models`, `train`, `completion`.

## generate

```bash
draw-things-cli generate --model sd_v1.5_f16.ckpt --prompt "a red cube" \
  --width 512 --height 512 --steps 8 --seed 1 --output out.png --no-download-missing
```

Key flags: `--model` (file id, name, `hf://owner/repo`, or HF URL), `--prompt` /
`--prompt-file`, `--negative-prompt`, `--image` (img2img init), `--strength`, `--steps`,
`--cfg`, `--width`/`--height`, `--seed`, `--frames` (video models → `.mov`/`.mp4` with
`--video-format`), `--config-json` (full **`JSGenerationConfiguration`**, merged over the
model's recommended settings), `--terminal-image` (inline preview in iTerm2/kitty),
`--offline`, `--download-missing`. Output to `.png` or `.mov`/`.mp4`.

**Controls over the CLI** go in `--config-json` (`{"controls":[…]}`) — but the same limits
as the HTTP API apply: only **depth** (auto-extracted) and **PuLID** work; pose/Redux/
FaceID/inpaint need the gRPC **hints**/**mask** channels (the CLI has no `--mask` and no
hint channel). For those, use the **ComfyUI bridge** — see
[`comfyui-bridge.md`](comfyui-bridge.md) and [`controlnet.md`](controlnet.md).

## models

```bash
draw-things-cli models list --downloaded-only      # inspect local model mappings
draw-things-cli models ensure --model flux_2_dev_q8p.ckpt   # download if missing
draw-things-cli models import <checkpoint|safetensors>      # import a local artifact
```

## train lora — fully automatable ✅

Headless LoRA training, no GUI. **Verified** (config resolves + dataset loads via
`--dry-run`).

```bash
draw-things-cli train lora \
  --model sd_v1.5_f16.ckpt --dataset ./dataset \
  --steps 500 --rank 16 --scale 1.0 --learning-rate 1e-4 \
  --save-every 100 --resolution 512 --name "my-lora" -o my_lora
```

- **Dataset:** a directory of images; a matching `.txt` next to each image is its caption
  (e.g. `fox01.png` + `fox01.txt`). Missing captions are fine.
- **Hyperparameters (flags):** `--steps`, `--rank`, `--scale`, `--learning-rate` (float,
  or a range like `[5e-5,1e-4]` / `5e-5:1e-4`), `--gradient-accumulation`,
  `--warmup-steps`, `--save-every` (0 = final only), `--seed`, `--clip-skip`,
  `--noise-offset`, `--caption-dropout`, `--resolution` / `--width`/`--height`,
  `--use-aspect-ratio` (bucket training), `--orthonormal-down`, `--cotrain-text-model`.
- **Full config:** `--config-json` in **`LoRATrainingConfiguration`** format (merged over
  defaults) for anything not exposed as a flag.
- **Output / resume:** `-o` (filename prefix, lands in the models dir as a `.ckpt`),
  `--name` (metadata display name), `--resume <checkpoint>`. With `--save-every N` you get
  step checkpoints — the same `*_<steps>_lora_f32.ckpt` pattern as the user's existing
  trained LoRAs.
- **Memory:** `--memory-saver minimal|balanced|speed|turbo`,
  `--weights-memory cached|justInTime`.
- **Automation aids:** `--dry-run` (validate + print the resolved config without training
  — ideal for CI/scripting), `--offline`, `--download-missing`.

So a training pipeline is just: assemble a captioned image folder → `train lora` with the
hyperparameters (or a `--config-json`) → the `.ckpt` appears in the models dir, ready to
use in `generate` or the app. Scriptable end to end.

## Fine-tuning helper scripts

Two bundled scripts wrap the full workflow (both stdlib-only, no pip deps):

### `scripts/caption.py` — auto-caption images for the dataset

Generates the matching `.txt` caption next to each image (the format `train lora` wants),
using any OpenAI-compatible **vision** endpoint — defaults to local **Ollama** with
`huihui_ai/qwen3-vl-abliterated:8b-instruct-q4_K_M`. Model, prompt, and endpoint are all
overridable, so it also works against OpenRouter/Together/etc.

```bash
scripts/caption.py photo.png                       # one image → photo.txt
scripts/caption.py ./dataset --prefix "ohwx, "     # whole dir, with a trigger word
scripts/caption.py ./dataset --overwrite --recursive
scripts/caption.py ./dataset --base-url https://openrouter.ai/api/v1 \
  --model qwen/qwen-2.5-vl-72b-instruct            # remote vision model
```

Flags: `--model`, `--prompt`, `--base-url`, `--api-key` (or `OPENAI_API_KEY` /
`OPENROUTER_API_KEY` / `TOGETHER_API_KEY`), `--prefix` (trigger word), `--ext`,
`--recursive`, `--overwrite`, `--dry-run`. Skips images that already have a caption unless
`--overwrite`. Strips `<think>` blocks from reasoning models.

**Caption models (local Ollama vision):** the default is `huihui_ai/qwen3-vl-abliterated:8b-instruct-q4_K_M`
(best quality, follows the comma-separated-line format). For fast bulk captioning there's
`qwen3vl-abl-2b-caption` — a 2b-instruct variant tuned with `num_ctx 8192` (≈3 GB VRAM vs
~21 GB at the 262144 default), `num_predict 256`, `temperature 0.3`. It's abliterated (no
content refusals) but, being 2b, tends to write prose paragraphs rather than tight tag
lines. Pass either via `--model`. These are **Ollama** models — see the `ollama` skill, not
[`models.md`](models.md) (which indexes Draw Things image checkpoints/LoRAs/ControlNets).

**Correcting captions:** when the model gets something wrong, feed it the truth instead of
re-rolling blindly — it keeps the accurate parts and fixes the error:

- `--context "TEXT"` — a fact/correction the model trusts over its own guess.
- `--draft "TEXT"` — a specific prior caption to revise (single image).
- `--revise` — batch: use each image's existing `.txt` as the draft to improve.

```bash
# one fix: "weapon" → Muffler Man, keeping the rest of the caption
caption.py art.png --context "the figure is a fiberglass Muffler Man statue, not a weapon"
# fix a recurring mislabel across a whole dataset
caption.py ./dataset --revise --context "the recurring giant is a Muffler Man statue" --overwrite
```

Verified: captioned the test fox as _"a red fox with orange fur, white chest and
black-tipped ears sits alert in snow…"_ in ~10 s on the local 8B model.

### `scripts/train_lora.py` — validate dataset + run training

Thin wrapper over `train lora`: checks the dataset (counts images, warns about any without
captions), builds the command, streams output, and reports the resulting `.ckpt` in the
models dir.

```bash
# caption then train, end to end:
scripts/caption.py ./dataset --prefix "ohwx, "
scripts/train_lora.py --dataset ./dataset --output ohwx_lora \
  --model sd_v1.5_f16.ckpt --steps 800 --rank 16 --save-every 200
# validate config first without spending GPU:
scripts/train_lora.py --dataset ./dataset --output ohwx_lora --dry-run
# forward any extra CLI flag after `--`:
scripts/train_lora.py --dataset ./dataset --output ohwx_lora -- --caption-dropout 0.1 --cotrain-text-model
```

> Known upstream issue: draw-things-community **#81** — a FLUX.1 [dev] LoRA-training run
> reportedly wrote only the initialization state to the checkpoint. Verify FLUX LoRA
> outputs; SD-family training is the safer bet until that's confirmed fixed. See
> [`ecosystem.md`](ecosystem.md).
