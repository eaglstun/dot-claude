# Project files, version control, and platform limits

## File types

| Extension         | What it is                                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------------------------- |
| `.toe`            | A whole project. Binary.                                                                                         |
| `.tox`            | One component saved out on its own — the reusable module format.                                                 |
| `.tox` (external) | A COMP whose `External .tox` parameter points at a file on disk, so the COMP's contents live outside the `.toe`. |

A `.toe` is a container; a `.tox` is a component you can version, share, and drop
into other projects. Any Base COMP can be saved with **right-click → Save
Component .tox**.

## Externalize everything you want to diff

The default `.toe` swallows all your Python into a binary blob. Two mechanisms
pull it back out:

**External Python for DATs.** On a Text DAT's parameters, set **File** to a `.py`
path and turn on **Sync to File** (write DAT → disk) or load from it. Now your
code is a real file you can edit in a real editor, lint, diff, and review. Do this
for every non-trivial script and every extension class.

**External `.tox` for components.** On a COMP, set **External .tox** to a path.
The COMP's contents are saved to and loaded from that file instead of living
inside the `.toe`. Good for modules shared across projects; also lets two people
work on different components without fighting over one binary.

Suggested layout for a new project:

```
project/
  project.toe
  modules/           # external .tox components
  scripts/           # .py files synced to Text DATs
  media/             # video, images, audio (probably gitignored or LFS)
  README.md
```

## Version control

The `.toe` is binary — git can store it but not merge it. Two workable approaches:

**1. Externalize + accept the binary.** Keep Python in `.py` files and components
in `.tox` files so the _meaningful_ diffs are readable, and let the `.toe` be an
opaque blob that only one person edits at a time. This is what most studios do.

**2. Expand for diffing.** The bundled CLI tools unpack a `.toe`/`.tox` into a
directory tree of individual node files:

```bash
TD=/Applications/TouchDesigner.app/Contents/MacOS
$TD/toeexpand project.toe            # → project.toe.dir/ (a directory structure)
$TD/toeexpand project.toe moviein1   # expand just a matching node
$TD/toeexpand -b project.toe         # print the build info the file was saved with
$TD/toecollapse project.toe.dir      # pack it back into a .toe
```

Expanded form is text-ish and diffable, which makes code review and "what changed
in this commit" actually possible. Some teams commit only the expanded directory
and collapse on checkout. It is not a merge tool — round-tripping through
`toecollapse` is reliable, hand-merging conflicting node files is not. Try it on a
throwaway copy before trusting it with real work.

`toeexpand -b` is also the quick way to find out which TD build saved a file
without opening it — useful when a `.toe` refuses to load.

Suggested `.gitignore`:

```gitignore
# TD incremental saves. NOTE the pattern: TD writes NewProject.1.toe — the digit
# goes BEFORE the extension, so `*.toe.[0-9]*` does not match anything. TD also
# rotates older increments into Backup/.
*.[0-9].toe
*.[0-9][0-9].toe
Backup/

# toeexpand output — regenerate on demand, never commit
*.toe.dir/
*.toe.toc
*.tox.dir/
*.tox.toc
*.bkp[0-9]          # toecollapse renames the original to .bkp1

# Media — large binaries; use LFS or keep them out of the repo
media/
*.mov
*.mp4
*.mxf
*.wav
*.aiff
*.exr

# Python bytecode. TD generates __pycache__ next to any external module it
# imports (e.g. an MCP bridge's modules/), inside YOUR repo.
__pycache__/
*.py[cod]

.DS_Store
```

Two of these were learned the hard way rather than guessed, both verified on
2026-08-09:

- **The increment pattern.** TD names backups `NewProject.1.toe`, not
  `NewProject.toe.1`. A `*.toe.[0-9]*` rule looks right and matches nothing.
- **`__pycache__`.** If any external Python lives in the project folder, TD
  compiles it on import and drops bytecode into your working tree. 15 `.pyc`
  files staged themselves on the first `git add -A` here.

TD writes numbered backup copies next to the project on save (configurable in
Preferences). Don't commit them.

## External Python packages

TD 2025 embeds **Python 3.11**. To use pip packages, install them for a matching
3.11 interpreter and add the path:

```python
# in an Execute DAT's onStart, or a startup script
import sys
sys.path.append('/path/to/site-packages')
```

Or set the **Python 64-bit Module Path** in `Preferences → General`. Packages with
compiled extensions must be built for **Python 3.11 and arm64** — a wheel from an
x86_64 or 3.12 environment will fail to import, usually with an unhelpful error.
The safest route is a dedicated venv created with a 3.11 arm64 interpreter, used
only to populate a site-packages folder you point TD at.

## The Palette

`Alt`-pinned panel on the left of the main window (or `Dialogs → Palette Browser`).
Ships with a large library of prebuilt components — Blend, Lister, Widgets,
WebRender, TDAbleton, and a **Snippets** browser with runnable examples for nearly
every operator. Before building something from scratch, look here; the Snippets in
particular are the fastest way to get a correct callback signature or an unfamiliar
operator's expected wiring.

## Licensing

TouchDesigner is free as **Non-Commercial**, with a resolution cap of **1280×1280**
on outputs and several features restricted or disabled. Commercial, Educational,
and Pro tiers lift those limits to varying degrees. The exact per-tier feature
matrix changes between releases — check `derivative.ca/licensing` rather than
relying on a remembered list, especially before promising a client that a feature
works.

The practical Non-Commercial gotcha: build at a resolution you can actually output.
Designing a 4K show on a Non-Commercial license and discovering the cap at install
time is a bad afternoon.

## What macOS doesn't have

Anything CUDA-backed is Windows + NVIDIA only and is either absent or non-functional
here:

- Nvidia Flow (fluid sim), Nvidia Background TOP
- RTX denoise / upscale / video effects
- Optical Flow TOP
- Hardware-accelerated NVENC/NVDEC encode/decode paths
- Third-party ops built against CUDA

Mac-side equivalents and alternatives: **Syphon** in place of Spout for
app-to-app frame sharing; **NDI** for network video either way; **HAP** as the
realtime playback codec (cross-platform, and the right choice on Mac where
hardware H.264 decode is less of a win than it looks); GLSL TOPs to hand-roll
effects that only exist as NVIDIA ops.

Before recommending or planning around any operator, confirm it exists on this
platform — the docs wiki notes platform restrictions on the operator's page.

## Where to look things up

- **Wiki / docs:** `docs.derivative.ca` — operator pages at `<Name>_TOP`,
  Python classes at `<Class>_Class`.
- **In-app:** right-click any operator → **Help** opens its wiki page. The **OP
  Snippets** browser (Help menu) has runnable examples per operator.
- **Forum:** `forum.derivative.ca` — the actual answer to most obscure questions,
  often from Derivative staff. Note the post date; TD's API has evolved and
  ten-year-old forum code frequently uses removed idioms.
