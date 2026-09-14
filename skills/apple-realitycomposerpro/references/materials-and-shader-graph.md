---
semantic_id: "sOdjSW41uZ3G7ZqgsCHn4tV8GiZL0AAP"
related_ids:
  - "wO5ibXM3vZ3E7ZukiCPf8l17AiOK0AAL"
  - "sOQJZW4xNQ3wybPiOGHnsNXbInZa8AAF"
---
# Materials and Shader Graph

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/building-materials-in-reality-composer-pro>
- <https://developer.apple.com/documentation/realitycomposerpro/applying-materials-to-an-asset>
- <https://developer.apple.com/documentation/realitycomposerpro/designing-materials-with-shader-graph>
- <https://developer.apple.com/documentation/shadergraph>

Fetched: 2026-08-19

Node catalog lives in **`shader-graph-nodes.md`**. This page is the material model, the
Inspector surface, and the runtime-parameter story.

## Five material types

| Shader | RealityKit type | Use for |
| --- | --- | --- |
| **Physically Based** | `PhysicallyBasedMaterial` | Realistic light-responsive surfaces |
| **Unlit** | `UnlitMaterial` | Color exactly as specified, ignores all lighting — UI overlays, emissive-looking surfaces |
| **Occlusion** | `OcclusionMaterial` | Invisible but writes depth — hides virtual content behind real or invisible surfaces, still casts/receives shadows |
| **Portal** | `PortalMaterial` | Works with the Portal component to render another world through a mesh — a window into elsewhere |
| **Shader Graph** | `ShaderGraphMaterial` | Fully custom, node-authored; the only type supporting arbitrary logic, animation, and **runtime parameter changes** |

New materials **default to Shader Graph**. Change the type in the Inspector's **Shader**
field. Physically Based, Occlusion, and Unlit are edited entirely in the Inspector;
**Portal and Shader Graph must be double-clicked open into the Graph Editor.**

Create one: Project Browser → Control-click → **New → Material**, or **`+` → Material**.

> Adding a Geometry Entity (Plane, Sphere, Box) auto-assigns `default_material`, typed as
> Shader Graph. Editing `default_material` changes **every** new geometry entity that uses
> it — instance it first (see `scenes-entities-prototypes.md`).

Materials show as a **paintbrush icon** in the Hierarchy and a thumbnail in the Project
Browser. You cannot select a material in the Viewport; select the entity and reassign under
**Model Component → Material Slots**.

## General Inspector options (all types)

- **Face Culling** — Back / Front / None. Discards hidden polygon faces.
  (`CustomMaterial.FaceCulling`)
- **Material** — the argument list defining overall appearance.
- **Reads Depth** — performs a depth test against RealityKit's depth buffer.
- **Writes Depth** — writes its own depth into that buffer.

Not every option exists on every type — Reads Depth does not apply to Occlusion materials.

## Physically Based options

**Blend Mode**: Opaque or Transparent (`CustomMaterial.Blending`); the rest of the panel
changes with it. **Opacity Scale** (0 = fully transparent, 1 = fully opaque) and **Opacity
Texture** appear only when Transparent.

Textures: Base Color, Roughness, Metallic, Normal, Clearcoat, Clearcoat Roughness,
Emissive, Specular, Ambient Occlusion.

Scalars: **Roughness Scale** and **Metallic Scale** (both 0–1, where roughness 1 = fully
rough / 0 = smooth, metallic 0 = non-metal / 1 = fully metallic).

**Base Color Tint** takes a color or a texture, in Display-P3, Linear Display-P3, sRGB, or
Linear sRGB. **If both tint and Base Color Texture are set, the tint tints the texture.**

**Opacity Threshold** — below this, RealityKit ignores opacity. `0.0` means no extra
masking; above `0.0` the material renders only where Opacity exceeds the threshold.

## Shader Graph material options

**Lighting Model** — the one Shader-Graph-specific Inspector control, and the useful lever
when you want to override rendering attributes without touching the surface output node:

| Value | Meaning |
| --- | --- |
| **Unspecified** | RealityKit infers the model from the graph's surface output node |
| **Lit** | Standard PBR shading |
| **Unlit** | Skips lighting, shows surface color directly |
| **Hair** | Anisotropic model tuned for hair strands |
| **Clearcoat** | Adds a transparent specular layer — car paint, lacquer |

> **Known bug worth knowing (Beta 3/4, 180306610):** subsurface scattering with SSS weight
> > 0 and specular roughness < 1 renders **black** on surfaces facing away from a
> directional or spot light, on both the RealityKit PBR and OpenPBR surface nodes — but
> *only* when the lighting descriptors are left **Unspecified**. Workaround: set Lighting
> Model to **Lit** and Specular Model to **GGX** or **GGX Anisotropy**.

Other node-level Shader Graph options:

- **Blend Mode** (Opaque / Alpha / Add) — overrides the inferred default. Left unset, the
  system infers one from what connects to the surface.
- **Apply Color Dithering** — stippling to fake smooth gradients and blends.
- **Increase Half Precision** — swaps a node for the generic-group member whose half
  connectors are upgraded to float. Column/row sizes are preserved and non-half connectors
  must match exactly; if no float counterpart exists it logs an info message and skips the
  node. Does not apply to input, output, or subgraph nodes.
- **Decrease Float Precision** — 32-bit float → 16-bit half, for performance and memory.

## Authoring in the Shader Graph editor

A new material opens with two nodes: **PreviewSurface** and **Output**.

The mental model Apple gives is explicitly Metal: nodes are variables, constants, and
functions; multiple typed versions of a node are function overloads.

**Which output pin you connect to decides what you are writing:**

| Output pin | Metal equivalent | Controls |
| --- | --- | --- |
| **Surface Shader** | Fragment shader | Surface appearance |
| **Geometry Modifier** | Vertex shader | The shape of the entity |

Node names enforce this. A node whose name starts with **Geometry Modifier** connects only
to the Geometry Modifier pin; one starting with **Surface** connects only to Custom
Surface. Generic operators like `Sin` or `If Equal` connect anywhere. Types must match — a
boolean output cannot drive a matrix input.

With no node selected, the Inspector shows the graph's own interface and Inputs.

## Runtime parameters — promoted inputs

Shader Graph values you can change **while the app runs**. Set the kind in the Input
Inspector (or Control-click the pin, then use the demote/promote commands):

| Kind | Mutable at runtime? | Cost | Maps to |
| --- | --- | --- | --- |
| **Uniform** *(default)* | Yes — polled each frame, no recompile | Cheapest to change | `Material.Parameters` |
| **Constant** | No — baked into the shader, opaque and immutable at runtime | Free | A constant node |
| **Function Constant** | Yes, but **triggers a full shader recompile**, after which the value is baked | Expensive to change | `MTLFunctionConstantValues` |

**All subgraph inputs are constant.** Graph inputs default to uniform.

Typical uses: a Boolean input driving conditional logic to switch emission on and off; a
`Float` input interpolating between two colors.

## Interoperability — MaterialX

Shader Graph follows **MaterialX 1.38** conventions so graphs read and write inside USD
alongside other DCC tools. It adds RealityKit-only nodes on top; some of those are
published as standard MaterialX definitions —
<https://developer.apple.com/download/files/MaterialX-definitions.zip>.

If an imported USDZ contains Shader Graph materials, RCP recreates them on import.
