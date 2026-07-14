# Draw Things — GitHub org repo map

Quick summary of every repo under [github.com/orgs/drawthingsai](https://github.com/orgs/drawthingsai/repositories)
(13 repos, snapshot **2026-06-01**). Grouped by relevance to this skill. Stars/language
are approximate and as-of the snapshot.

## Open issues & PRs (snapshot 2026-06-01)

| Repo                  | Issues | PRs | Notable                                                                                                                                                                                                                                              |
| --------------------- | ------ | --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| draw-things-community | 62     | 1   | CLI feature reqs — **#79 embed prompt/settings into image metadata** (what this skill already does via exiftool), #80 import models from disk; #81 FLUX.1 LoRA-training checkpoint bug; #78 Anima 8-bit blue screens; PR #83 memcpy bounds-check fix |
| homebrew-draw-things  | 0      | 0   | —                                                                                                                                                                                                                                                    |
| media-generation-kit  | 2      | 0   | #2 Swift CLI build error, #1 tensor dim-mismatch assertion — the Swift SDK looks rough                                                                                                                                                               |
| community-scripts     | 0      | 4   | pending new scripts: StyleSweeper, change-clothes, Dynamic Prompts update, neg-prompt for auto workflow                                                                                                                                              |
| community-models      | 2      | 9   | busy queue of model/LoRA additions (Anima, Lustify SDXL, BananaSplitz…); #30 HiDream-O1 request                                                                                                                                                      |
| community-docs        | 0      | 0   | —                                                                                                                                                                                                                                                    |
| draw-things-comfyui   | 1      | 0   | #4 "Does not list custom models" — gRPC bridge gotcha                                                                                                                                                                                                |
| ComfyUI               | 0      | 0   | fork                                                                                                                                                                                                                                                 |
| taesd                 | 0      | 0   | —                                                                                                                                                                                                                                                    |
| taehv                 | 0      | 0   | —                                                                                                                                                                                                                                                    |
| PythonKit             | 0      | 0   | fork                                                                                                                                                                                                                                                 |
| pytorch               | 0      | 1   | PR #1 "Changes for PyTorch to work in Draw Things" (the DT build patch)                                                                                                                                                                              |
| scipy                 | 0      | 0   | fork                                                                                                                                                                                                                                                 |

Counts come from the GitHub API (issues endpoint, PRs separated by the `pull_request`
key). Issue/PR numbers are clickable as `…/<repo>/issues/<n>` or `/pull/<n>`.

## Core engine & headless interfaces

- **[draw-things-community](https://github.com/drawthingsai/draw-things-community)** — C/Swift, ★450, actively pushed.
  The main monorepo for the Draw Things engine. Top-level dirs: `Apps`, `Libraries`,
  `Tools`, `Vendors`, `Scripts`, `external`. **This is where the headless surface lives:**
  the `draw-things-cli` binary (the one in the Homebrew tap), the gRPC server, and the
  gRPC **`.proto`** definitions. The source of truth for CLI/gRPC behavior — read this to
  settle the mask/moodboard/control questions the HTTP API can't answer.

- **[homebrew-draw-things](https://github.com/drawthingsai/homebrew-draw-things)** — Ruby, ★4.
  Homebrew tap. One formula, `draw-things-cli` (built from draw-things-community).
  Install: `brew tap drawthingsai/draw-things && brew install draw-things-cli`. **Installed.**

- **[media-generation-kit](https://github.com/drawthingsai/media-generation-kit)** — Swift, ★15.
  The **`MediaGenerationKit` Swift package** + an example `media-generation-kit-cli`
  client — a Swift SDK for programmatic media generation (the gRPC-client SDK for building
  apps against the engine). Own docs at drawthingsai.github.io/media-generation-kit.

## In-app scripting & content catalogs

- **[community-scripts](https://github.com/drawthingsai/community-scripts)** — JavaScript, ★32.
  Source for the app's **Scripts** feature. JS workflows using the `canvas` / `pipeline` /
  `configuration` API (`loadMaskFromSrc`, `addToMoodboardFromSrc`,
  `extractDepthMapFromSrc`, `findControlByName`, `preserveOriginalAfterInpaint`). Examples:
  `edit-background`, `style-transfer`, `creative-upscale`, `detailer`,
  `sd-ultimate-upscale`, `flux-auto-workflow`, `wildcards`. **This is the surface that can
  drive the mask/moodboard/preprocessed controls the HTTP API and CLI can't** (see
  [`controlnet.md`](controlnet.md) and `../output/results.md`).

- **[community-models](https://github.com/drawthingsai/community-models)** — Python, ★84.
  Source repo managing the **"Community" section of models & LoRAs** in the app — the
  catalog/registry of downloadable checkpoints with their recommended settings/metadata.

- **[community-docs](https://github.com/drawthingsai/community-docs)** — ★24, last pushed 2024.
  Documentation source for **docs.drawthings.ai**. Useful because the live docs site is
  JS-rendered (WebFetch returns empty) — the readable markdown lives here.

## Integrations

- **[draw-things-comfyui](https://github.com/drawthingsai/draw-things-comfyui)** — TypeScript, ★20.
  Official **ComfyUI extension** bridging ComfyUI → Draw Things over **gRPC**. Requires the
  app's API Server set to Protocol gRPC (or `gRPCServerCLI`) + "Enable Model Browser". It
  does ControlNet/inpaint over gRPC — strong evidence the gRPC interface exposes the
  canvas/mask/control plumbing the HTTP API omits.

- **[ComfyUI](https://github.com/drawthingsai/ComfyUI)** — fork, ★6, 2024.
  Fork of `comfyanonymous/ComfyUI` (the node-based diffusion GUI), supporting the extension
  work above.

## Tiny autoencoders (fast VAE preview/decode)

- **[taesd](https://github.com/drawthingsai/taesd)** — Python, ★0.
  Tiny AutoEncoder for Stable Diffusion (and other image models) — small/fast VAE for quick
  latent↔pixel decode/preview.
- **[taehv](https://github.com/drawthingsai/taehv)** — Python, ★0.
  Tiny AutoEncoder for Hunyuan Video (and other video models) — the video counterpart of taesd.

## Dependency forks (build mirrors, not Draw Things code)

- **[PythonKit](https://github.com/drawthingsai/PythonKit)** — fork, ★3, 2024. Swift↔Python interop framework (build dependency).
- **[pytorch](https://github.com/drawthingsai/pytorch)** — fork, ★1, 2024. PyTorch mirror.
- **[scipy](https://github.com/drawthingsai/scipy)** — fork, ★1, 2024. SciPy mirror.

## Where to look for what (this skill)

| Need                                           | Repo                    |
| ---------------------------------------------- | ----------------------- |
| CLI / gRPC behavior, the `.proto`              | `draw-things-community` |
| Install the CLI                                | `homebrew-draw-things`  |
| In-app scripting API (mask/moodboard/controls) | `community-scripts`     |
| Model catalog & recommended settings           | `community-models`      |
| Readable API/scripting docs                    | `community-docs`        |
| Headless full-control integration (gRPC)       | `draw-things-comfyui`   |
| Swift SDK for embedding                        | `media-generation-kit`  |
