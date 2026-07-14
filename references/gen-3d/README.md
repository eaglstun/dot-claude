---
topic_id: "v2:DEIK"
topic_path: "model-runners/model-makers"
semantic_id: "bmhbtXrWUkcNxWNIIG4KV2ty9raMMAAJ"
related_ids:
  - "Xk0bvdbWEkcN1WJodG5DB2NydLaMMAAO"
  - "XnxTGf_GEgctzVJodntHVXF0dbSEEAAB"
---
# Generative-3D references — local notes

Source-cited working notes for the **generative-AI 3D asset pipeline** — prompt/image in, a
rigged + (optionally) animated **GLB** out, for the native iOS app. This is the generative
counterpart to the procedural model-makers (`ios-model-maker` hand-codes low-poly vertex arrays;
this path calls a hosted REST API and gets back a full mesh with a skeleton). Written and
consulted by the `gen-3d-model-maker` agent; each file cites its origin (vendor API doc URL or a
`file:line` in this repo) and is grounded — no notes from memory. Reuse before re-deriving.

**Scope boundary:** these cover _producing and rigging the asset_ and the _runtime reality_ it
has to land in. They do **not** make the renderer play it — the native Metal skinning runtime
that animates a rigged GLB is a separate build, spec'd in `native-skinning-runtime.md`.

## Index

- **tripo-api.md** — Tripo3D REST API: the concrete endpoint contract (the async
  generate → rig → animate/retarget pipeline, polling, outputs).
- **meshy-api.md** — Meshy REST API: the concrete endpoint contract (text/image-to-3D + rig +
  animate, polling, GLB/PBR outputs) and where Meshy diverges from Tripo for vendor choice.
- **gltf-rigged-glb-format.md** — the glTF 2.0 / GLB rigged-model format contract: GLB container,
  accessors, skin/skeleton, JOINTS_0/WEIGHTS_0, animations — what a "rigged GLB" contains.
- **rig-and-animate-apis.md** — the generative rigged + animated model APIs across vendors, and
  the iOS runtime reality a rigged GLB has to fit into.
- **generation-cost-and-licensing.md** — the cost + commercial-license picture for Tripo and Meshy:
  credit costs, tiers, and the CC BY 4.0-vs-ownership IP terms that gate shipping under the LLC.
- **native-skinning-runtime.md** — build spec for the native Metal skinning runtime (linear
  blend skinning) that plays a rigged GLB — the separate downstream build, not this agent's job.
