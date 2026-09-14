---
semantic_id: "sMDBZWYxNZ_2ybJjvmGvclTzEkda4AAH"
related_ids:
  - "sOQJZW4xNQ3wybPiOGHnsNXbInZa8AAF"
  - "MmXDYy1zPYfSSbJLeBqr4lTFEld6cAAA"
---
# Reality Composer Pro 3 — the app, the workspace, and the Xcode link

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro>
- <https://developer.apple.com/documentation/realitycomposerpro/realitycomposerpro-essentials-linkingxcodeproject>
- <https://developer.apple.com/documentation/realitycomposerpro/realitycomposerpro-essentials-configuringprojectworkspace>
- <https://developer.apple.com/documentation/realitycomposerpro/realitycomposerpro-essentials-workspaceoverview>
- <https://developer.apple.com/documentation/realitycomposerpro/realitycomposerpro-essentials-grapheditoroverview>
- <https://developer.apple.com/documentation/realitycomposerpro/realitycomposerpro-essentials-previewcontentrunsimulations>
- <https://developer.apple.com/documentation/realitycomposerpro/working-with-the-reality-composer-pro-assistant>

Fetched: 2026-08-19

## What changed in version 3 — read this before anything else

**Reality Composer Pro is no longer part of Xcode.** Version 3 is a standalone app
downloaded from the Apple Developer website. Any instruction of the form "open Xcode →
open the `.rkassets` package to launch Reality Composer Pro" describes version 1 or 2.

| Requirement | Value |
| --- | --- |
| Mac | Apple silicon **only** |
| macOS | Tahoe **26.5 or later** |
| Xcode (for the project link) | **27** |
| Ship state | **Beta** — Beta 4 is the newest release note published |
| Asset Generation (Assistant) | macOS **27** only |

A second reversal: **RCP is not a visionOS tool anymore.** "Run with Xcode" generates a
*Universal* app for every platform that supports RealityKit — iOS, iPadOS, macOS,
visionOS, and tvOS.

## The four panes

Locate assets in the **Project Browser**, organize them in the **Hierarchy**, edit them in
the **Viewport**, refine components in the **Inspector** (which also hosts the Preview
area). That loop is the whole editor.

- **Hierarchy** — every asset, component, and entity in the scene currently open in the
  Viewport. Add/remove/copy/rename/drag directly; Control-click for the full menu.
  Per-item **Lock** and **Hide** are *editor-only* and do not affect exported files — to
  actually take an entity out of the build, Control-click → **Deactivate**.
  The bottom icons add entities, toggle **Show Components**, and **Filter (⌘F)**, which
  searches components as well as entity names.
- **Project Browser** — files, folders, assets. Double-clicking an asset opens it in a new
  Viewport tab. Toolbar: New Folder, New Asset, Import Asset, back/forward, list vs. grid,
  thumbnail size, search.
- **Viewport** — Q/W/E/R map to Select, Move, Scale, Rotate. Manipulator axes are
  **red = X, green = Y, blue = Z**, gray center = free. Scroll to zoom, Option-drag to
  orbit, drag to marquee-select, Shift-click to multi-select.
- **Inspector** — components on the selected entity, or inputs/outputs of the selected
  graph node; also asset metadata such as USD import options. **Add Component** at the
  bottom right (or press Space).

### Viewport visualization controls

- **Enable Snapping** + **Snap Distance**; **Transform Space** (World vs. Local);
  **Pivot Point** (First Selected / Last Selected / Center / Bounding Box).
- **Select Camera** — only `Default Camera` exists until an entity carries a Camera
  component.
- **Filter Component Debug Visualization** — overlays per component:
  `CollisionComponent` draws collision shapes, `PointLightComponent` draws the attenuation
  radius as a sphere, `IKComponent` draws bones and joints. Also
  `CharacterControllerComponent`, `DirectionalLightComponent`, `DockingRegionComponent`,
  `ModelComponent`, `SpotLightComponent`, `VirtualEnvironmentProbeComponent`.
- **Rendering Visualization Modes** — isolate one channel:
  - *Geometry*: Normals, Tangent, Bitangent, Texture Coordinates.
  - *Material*: Base Color, Roughness, Metallic, Ambient Occlusion, Specular, Emissive,
    Clearcoat, Clearcoat Roughness.
  - *Output*: Final Color, Final Alpha, Lighting Diffuse, Lighting Specular.

### Lightmap baking

Inspector → **Lighting tools** → Bake Quality (Low / Medium / High / Production) →
**Bake Lightmap** or **Capture Environment**. Inspect results in **Tab → Lightmap
Preview**. The same Lighting tools panel is where you batch-generate navmeshes.

## Workspaces and tabs

Multiple workspaces, each with multiple tabs, each keeping **its own dock layout**.
Double-clicking an entity or asset in the Project Browser opens it in a *new workspace*.

**Tab → New Tab** offers: Behavior Tree Parameters, Console\*, Context, Graph, Hierarchy\*,
Inspector\*, Lightmap Preview, List, Parameters, Preview, Project Browser\*, Simulate,
Skeleton, Tags, Viewport\*. (\* = open by default.)

Drag a tab onto a dock to move it, including between the Viewport tab bar and the Project
Browser tab bar.

## The Graph Editor — shared across all four graph types

Script Graph, Shader Graph, **and** Animation Graph (plus Behavior Tree and Compute Graph)
all use the same canvas with the same controls. Learn it once.

- **Open**: double-click a graph asset, or **Tab → New Tab → Graph** and drag a graph file in.
- **Add a node**: press **N** or Space; or Control-click → Add Node; or drag off a
  connector and release in empty space — that last one filters the selector to only nodes
  compatible with what you are connecting.
- **Rename** any node by clicking its name. Do it: `Wait at Door` reads better than `Wait`.
- **Connect**: drag output → compatible input. Incompatible ports refuse the connection.
  Input/Output/Subgraph nodes have a **`+`** connector; dragging from it names and types
  the new port automatically from whatever you connect. Whether you can add extra
  outputs is graph-type-dependent — **Shader Graph does not allow additional outputs.**
- **Subgraphs**: select nodes → Control-click → **Compose Subgraph**.
  **Decompose Subgraph** inlines it back and rewires external connections.
- **Comments**: Control-click a node → Add Comment Box, or select several and press **C**.
  Deleting a comment does *not* delete its nodes. Duplicating a comment copies the nodes
  but **drops all their connections**.
- **Layout**: Control-click canvas → Clean up, Zoom Fit; with a selection → Align,
  Distribute.

## Linking an Xcode project

Launch Control toolbar: switch **Simulate → Run with Xcode**, then **Link an Xcode
project**. Install the helper when prompted.

New project options: Organization Identifier, Bundle Identifier, Initial Entity (defaults
to `World`), and **Immersive Space**:

| Immersive Space | Result |
| --- | --- |
| None | Windowed — Shared Space on visionOS, a normal window elsewhere |
| Mixed | Content alongside passthrough |
| Progressive | You control how much surroundings remain visible |
| Full | Only your content |

RCP creates a parent folder for the Xcode project automatically. For an *existing* project,
use **Link Existing Project**, then open the Xcode project, build it, **and restart Reality
Composer Pro**.

### Custom plugins (components, timeline actions, Script Graph nodes)

**Reality Composer Pro → Project Settings → Build Settings → Plugin Directory**, pointing
at your Xcode project folder. Linking a project with custom components fills this in
automatically and wires it to the Derived Data path, so editing Swift in Xcode recompiles
plugins that RCP picks up. **Restart RCP after linking to reload plugins.** Your components
then appear in the Add Component list; custom Sequencer actions appear in the Actions list
marked with a wrench icon.

## Preview vs. Simulate vs. Run

Three different things, easy to confuse:

| Surface | Needs Xcode link? | What it gives you |
| --- | --- | --- |
| **Preview tab** | No | Static look of the selected entity in a simulated visionOS or Mac environment |
| **Simulate** (Viewport) | No | Runs the scene in-editor — Script Graph entry points fire, particles emit, sequences play |
| **Preview on Device** | No | Pushes to a connected device (Vision Pro needs the *Reality Composer Pro Preview* app) |
| **Running Destinations** | **Yes** | Compiles and runs the real app on device or simulator — real views, cameras, game controllers, live code |

First compile per destination is slow; subsequent ones are not.

## Loading a scene from Swift

A Reality Composer Pro package defines a global bundle constant named after the project
plus `Bundle`. Xcode's visionOS template names the project `RealityKitContent`, giving
`realityKitContentBundle`:

```swift
RealityView { content in
    if let scene = try? await Entity(named: "Biplane",
        in: realityKitContentBundle) {
        myDataModel.add(scene)
        content.add(scene)
    }
} update: { content in
    // ...
}
```

`RealityView` has no `scene` property the way `ARView` does — **keep your own reference to
the root entity in your data model**, as the snippet does, or you lose access to the
content you just added.

## The Assistant (AI model provider)

Inspector → **Assistant** tab → gear → **Add a Model Provider**: URL, optional API Key, API
Key Header, Description. Any compatible provider; add as many as you like. Multiple
Assistant tabs can run different prompts at once (**Tab → New Tab → Assistant**).

It answers feature questions, generates 3D assets and materials from prompts or attached
images, and can reorganize the scene hierarchy. Generated output lands in **Generated
Assets** and **Generated Materials**.

Three cautions Apple states outright:

1. Prompts, conversation history, and any attached image go **to the configured provider**.
   Don't attach images containing personal information.
2. Keep the API key out of source control.
3. 3D model generation wants **≥ 32 GB unified memory**; less means significantly longer
   generation. And **Asset Generation requires macOS 27** regardless of memory.
