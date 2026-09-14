---
semantic_id: "IGQLSe5Vv8lYbfoysmOP8lI-ClJK8AAK"
related_ids:
  - "okdJYcYdt13ubbvyNiOP4tOeAndK8AAK"
  - "sOdjSW41uZ3G7ZqgsCHn4tV8GiZL0AAP"
---
# Scenes, entities, assets, and the prototype/instance model

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/realitycomposerpro-essentials-addingentitiestoscene>
- <https://developer.apple.com/documentation/realitycomposerpro/realitycomposerpro-essentials-understandingprototypes>

Fetched: 2026-08-19

## Entities and the ECS

Reality Composer Pro is a front end for **RealityKit's Entity Component System**. Every
entity has a position, orientation, and scale even with no visual representation, and
everything it *does* comes from components you attach.

Create an entity two ways:

- **Project Browser → `+` → Entity** — creates an entity *asset* (a file).
- **Hierarchy → Control-click an entity → Add Child Entity** — creates a non-asset entity
  that lives only in this scene.

To reopen a closed scene, double-click its entity file. To delete a scene, delete the file.

Add components in the Inspector: select the entity → **Add Component** (or press Space).
The list contains RealityKit's built-ins plus any custom components in the Sources folder
of your RCP Swift package — see the Xcode plugin-directory setup in
`workspace-and-xcode.md`.

## Importing assets

**File → Import File**, Project Browser → Control-click → Import File, the Import icon, or
plain drag-and-drop from Finder. Dependencies come along with the asset.

Four import behaviors that trip people up:

1. **Imported assets are read-only.** RCP converts imported `.usd` into entity assets and
   **never propagates changes back to the source `.usd`** — though it offers explicit
   export-back options. Legacy projects import into RCP's own project file, not `.usd`.
2. **Not every asset becomes an entity.** Images don't. Dragging a PNG into the scene does
   nothing; images are used *indirectly*, e.g. as a Shader Graph texture source.
3. **Unused assets still ship.** Assets in the project but in no scene are still compiled
   into your app and loadable at runtime. RCP compiles to `.reality` files.
4. **Deactivated entities do not ship.** Control-click → **Deactivate** grays the entity
   out in the Hierarchy, hides it in the Viewport, keeps it in the project, and excludes it
   from the app bundle. **Activate** brings it back. This is different from the Hierarchy's
   hide/lock icons, which are purely editor-side.

## Composing and re-parenting

Drag from the Project Browser into the Viewport or Hierarchy to instantiate. Re-parent by
dragging an entity onto its intended parent in the Hierarchy; drag onto the **Root**
transform at the top to make it the scene root.

Transform numerically in the Inspector's Transform component. **Option-click-drag over a
numeric field to increment it while dragging.**

Some things in the Hierarchy — scopes, materials, node graphs — are not transformable in 3D
space at all.

## Prototypes, instances, and overrides

This is the concept most worth getting right, because it silently determines whether an
edit affects one object or every copy of it.

- A **prototype** is the source asset. An **instance** is a placement of it.
- Editing the **prototype** propagates to every instance in the project.
- Editing an **instance** creates an **override** on that instance only. Overrides show as
  a small dot next to the icon in the Hierarchy.
- Revert one with Control-click → **Remove Override**.

**The trap:** when you assign a prototype *directly* to a component — a material into a
model component, say — RCP may not create an instance for you, so every "tweak" you make is
editing the prototype and changing every other user of it. To get an instance, Control-click
the material in the Project Browser → **Instance**, then assign *that*.

Create an instance explicitly: Project Browser → Control-click the prototype →
**Instantiate**. Add it to a scene by dragging it in, or Hierarchy → Control-click →
**Add Child Entity → From Asset**.

### Reconciling a diverged instance

| Command | Effect | Use when |
| --- | --- | --- |
| **Propagate** | Instance's values overwrite the prototype, so every other instance updates | This instance is the one that looks right |
| **Reset** | Discard local overrides, keep the prototype link | The experiment failed; stay linked |
| **Make Unique** | Sever the link; keep current values as a standalone copy | Tracking the prototype no longer helps |

Propagate and Reset are available from **both** the Inspector and the Hierarchy.
**Make Unique is Hierarchy-only.**

### Swapping the prototype under an instance

Select the instance → Inspector → click the prototype field → pick a different prototype.
The instance **keeps its existing overrides**, now applied on top of the new prototype.
Delete any override that no longer makes sense against the new source.

Subgraphs in the Graph Editor follow the same model — Convert to Prototype Subgraph, Open
Subgraph Prototype, Open Subgraph Instance, Remove Node Override.
