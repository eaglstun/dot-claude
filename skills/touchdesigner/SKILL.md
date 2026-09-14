---
name: touchdesigner
description: 'TouchDesigner reference — the operator families (TOP/CHOP/SOP/MAT/DAT/COMP/POP) and how data crosses between them, the Python API (op(), me, parent(), par access, custom parameters, extensions, storage), the callback DATs, cooking and GPU performance, and project/file workflow (.toe, .tox, externalized scripts, toeexpand, version control). Also covers the touchdesigner MCP bridge for driving a LIVE session — building networks with execute_python_script, reading real parameter names, and seeing renders via get_top_image, and point clouds / depth capture (PLY sequences, Record3D, the 2025 POP family). Use when writing or debugging TouchDesigner Python, wiring a network, choosing which operator does a job, diagnosing a slow or non-cooking network, setting up a .toe project for git, or when the MCP bridge won''t connect. Also covers this machine''s install: 2025.33070 on Apple Silicon macOS, where Vulkan/MoltenVK replaces the NVIDIA/CUDA-only operator set.'
metadata:
  version: 1.1.0
  public: 'true'
  semantic_id: F6-pI0kqUJVt-Vl_7PalyvasfO8okAAI
  related_ids: '["LI07MXMzQp_N2StDZ36nq6atCO-z8AAE","3_SU5xJ60Aeh6RtLdnKw1uHIMO6w0AAC"]'
---

# TouchDesigner reference

Notes for working in TouchDesigner — the node-based visual programming environment
from Derivative, used for realtime video, generative graphics, projection mapping,
audio-reactive work, and installation control.

This shelf is a reference, not a tutorial. It assumes you can find your way around
the UI and answers the questions that come up while actually building: _which
operator, how do I get data from A to B, why isn't this cooking, what's the Python
for this, how do I keep this in git._

## This machine

Verified from the install on 2026-08-09:

| Fact               | Value                                                           |
| ------------------ | --------------------------------------------------------------- |
| Version            | **2025.33070**                                                  |
| App path           | `/Applications/TouchDesigner.app`                               |
| Bundled Python     | **3.11** (`Contents/Frameworks/Python.framework/Versions/3.11`) |
| Platform           | macOS (Darwin 25.5), Apple Silicon                              |
| Graphics backend   | Vulkan via MoltenVK (`Contents/Resources/vulkan`)               |
| CLI utilities      | `Contents/MacOS/toeexpand`, `Contents/MacOS/toecollapse`        |
| Bundled frameworks | Syphon, CEF (Web Render), Alembic, AJA, OpenSubdiv              |

**macOS consequence that bites people:** anything CUDA-backed is Windows/NVIDIA
only. No Nvidia Flow, no RTX denoiser/upscaler, no Optical Flow TOP, no
CUDA-dependent third-party ops. Substitute or work around — see
`references/project-workflow.md`. Syphon is the Mac frame-sharing path (Spout is
the Windows one).

Python 3.11 is the version to match when installing external packages into the TD
site-packages path or pointing TD at a venv.

## The mental model

A `.toe` project is a tree of **components** containing **operators**, and every
operator belongs to one of seven families. The family determines what kind of data
flows on its wires, and **wires only connect within a family**. Crossing families
requires a conversion operator. That single rule explains most of the network
diagrams you'll ever see.

| Family   | Suffix            | Carries                                             | Runs on        |
| -------- | ----------------- | --------------------------------------------------- | -------------- |
| **TOP**  | Texture Operator  | 2D image / texture data                             | GPU            |
| **CHOP** | Channel Operator  | numeric channels & samples (audio, motion, control) | CPU (some GPU) |
| **SOP**  | Surface Operator  | 3D geometry (points, prims)                         | CPU (few GPU)  |
| **MAT**  | Material Operator | shaders/materials applied to geometry               | GPU            |
| **DAT**  | Data Operator     | text, tables, scripts, callbacks                    | CPU            |
| **COMP** | Component         | containers: 3D objects, UI panels, subnetworks      | —              |
| **POP**  | Point Operator    | points/particles held on the GPU (2025+)            | GPU            |

**POPs are new and easy to miss.** Verified on this install: `len([n for n in
dir(td) if n.endswith('POP')])` returns **103** operators — a full family added in
the 2025 builds, giving point and particle geometry a GPU-resident path that SOPs
(CPU) never had. If a task involves large point counts, point clouds, or
particles, check the POP family before reaching for `Copy SOP` or instancing.

Everything **cooks** — recomputes — only when something it depends on changed, once
per frame at most. Understanding _why_ an operator did or didn't cook is the core
debugging skill; `references/performance.md` covers it.

## Where to look

| Question                                                                                                                           | File                             |
| ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Which operator does X? How do I get CHOP data into a TOP? What's a Null for?                                                       | `references/operators.md`        |
| `op()`, `me`, `parent()`, reading/writing parameters, custom params, extensions, storage, expressions                              | `references/python-api.md`       |
| Callback DATs (Execute, CHOP Execute, Parameter Execute, Panel Execute), Timer/Replicator callbacks, run() and deferred execution  | `references/callbacks.md`        |
| Why is this slow / not cooking? GPU memory, resolution, Info CHOP, Perform mode                                                    | `references/performance.md`      |
| `.toe` vs `.tox`, externalizing Python, `toeexpand`, git strategy, licensing limits, macOS gaps                                    | `references/project-workflow.md` |
| Point clouds, PLY sequences, Record3D iPhone LiDAR/TrueDepth capture, the POP family | `references/point-clouds.md` |
| Driving a LIVE session over the MCP bridge — setup, tools, `execute_python_script` practice, `get_top_image`, why it won't connect | `references/mcp-bridge.md`       |

## Ground rules when working in this environment

1. **The official docs are `docs.derivative.ca`** (the wiki). Operator pages live at
   `docs.derivative.ca/<Name>_TOP` etc. Python class pages at `docs.derivative.ca/<Class>_Class`.
   When a parameter name or method signature matters, check there rather than
   guessing — TD's API has a lot of near-miss names.
2. **Parameter names in Python are not what the UI shows.** The UI label is
   "Resolution"; the parameter is `par.resolutionw` / `par.resolutionh`. Hover a
   parameter in the UI to see its real name, or use the Parameter/OP Snippets.
3. **Custom parameters are capitalized, built-ins are lowercase.** `n.par.Speed` is
   one you made; `n.par.tx` is built in. This is a real convention, not a style
   choice — it's how TD prevents collisions.
4. **Never assume an operator exists on macOS.** Check `references/project-workflow.md`
   before recommending anything from the NVIDIA family.
