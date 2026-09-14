---
semantic_id: "8sZP52pzF57GdRrgcqst0Xj4CnZioAAH"
related_ids:
  - "8uxPZ85y98lUaRaxNaPn41B7AnZKgAAO"
  - "csRLRSdXOYycaY_o4KFj03A9CidqwAAB"
---
# Animation Sequences — the timeline, tracks, actions, and Motion Path

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/creating-animation-sequences>
- <https://developer.apple.com/documentation/realitycomposerpro/building-multi-track-animation-sequences>
- <https://developer.apple.com/documentation/realitycomposerpro/creating-animation-sequences-for-autoplay>

Fetched: 2026-08-19

A **Sequence** is a timeline asset choreographing animation over time. It is a different
system from the **Animation Graph** (a state machine — see `animation-graph.md`); a Sequence
is a fixed arrangement in time, a graph is a runtime decision structure.

## The Root Entity rule — read this first

> **A Sequence appears as a selectable clip in an entity's Animation Library Component only
> if that Sequence's Root Entity is that same entity, or its prototype.**

This catches almost everyone on the first attempt, and **it fails silently**. Put the
Animation Library Component on the wrong entity and the Sequence just isn't in the
dropdown, with no error explaining why. With no eligible clips at all, the UI says
"No entries found in Animation Library Component for this entity." From editor scripting,
`edit_entry_in_animation_library_component` reports "no animations available."

The component has to live on the entity the Sequence is rooted at — **not a parent, not a
child, not another entity referencing the same assets.** There are exactly two fixes:

1. Move the Animation Library Component onto the Sequence's actual Root Entity, or
2. Recreate the Sequence with its Root Entity set to match where the component already is.

Which one is right depends on which side you set up wrong. Either way one side must change.

## Creating a Sequence

Project Browser → Control-click a folder → **New → Animation → Sequence** → name it → under
**Set Target Entity**, click **Choose** and pick the entity (the search box helps). To
reopen, double-click the sequence — it opens with its entity.

**Sequence settings:**

- **Root Entity** — the targeting scope. Tracks can animate the root itself or any of its
  children. Setting it to `world` lets tracks target anything under `world`.
- **Speed** — playback multiplier for the whole sequence (1 = normal, 2 = double).

## Tracks and sub-tracks

**Every main track targets exactly one entity, chosen explicitly.** Click **`+`** next to
the track name, click the entity in the Preview viewport, confirm in the picker banner.

**Sub-tracks skip the picker** — click **`+`** on the right of a main track's header and the
sub-track inherits the parent track's entity. Use them to spread several actions on the same
entity across rows instead of stacking them, which keeps the timeline readable once a track
collects audio cues, visibility toggles, and a Motion Path.

**Mute** disables a track without deleting it — the way to isolate one action type while
tuning the others.

## The Animation Clips panel

Lists animations compatible with the open sequence; drag clips onto tracks. Its
**Hierarchy** tab shows the entity hierarchy of the sequence's entity — useful for finding
a deeply nested child.

**Editing a clip by dragging its edges:**

| Drag | Sets |
| --- | --- |
| Left edge | **Trim Start** |
| Right edge, top | **Repeat Mode** and **Repeat Duration** |
| Right edge, bottom | **Trim End** |
| Right edge, bottom + **Option** | **Speed** |
| Right edge (on an *action*) | **Duration** |

**Clip properties:** Trim Start, Trim End, Delay (seconds before playing), Repeat Mode
(None / Repeat / **Auto Reverse** — forward then backward), Repeats Forever, and Repeat
Duration (used when repeating with Repeats Forever off).

**Display options** (the **…** menu): Units — Frames or Seconds; Snap — Nodes to Ruler,
Nodes to Nodes, Playhead to Ruler.

## Actions

Five built-ins. Every action's Inspector group starts with **Track Entry Name, Delay,
Duration**; several depend on a component already existing on the target entity, and offer
an **inline add button** in the Inspector when it's missing.

| Action | Depends on | RealityKit type |
| --- | --- | --- |
| **Play Audio** | Audio Library Component | `PlayAudioAction` |
| **Enable/Disable Entity** | nothing | `SetEntityEnabledAction` |
| **Billboard Blend In/Out** | Billboard Component | `BillboardAction` |
| **Motion Path** | nothing | — |
| **Custom Action** | a Custom Action Definition plugin | — |

**Play Audio** adds Gain (dB), a **Controlled Playback** toggle, and an **Audio Resource**
picker. That picker lists *only* named references already on an Audio Library Component
belonging to the target entity. End to end: select the entity → Add Component → **Animation
→ Audio Library** → **`+` Named Audio Reference** → name it and assign the imported asset →
drag Play Audio onto a track → set Audio Resource to that name.

**Enable/Disable Entity** is just Track Entry Name, Delay, and an **Is Enabled** toggle. No
component dependency — visibility is a base entity property. Good for reveals, disappearing
effects, or switching on a particle system right before a Motion Path moves through it.

**Billboard Blend In/Out** adds **Transition In** and **Transition Out** (seconds within the
action's Duration) controlling how long the blend takes to appear and to fade.

### Custom Actions

Set **Project Settings → Build Settings → Plugin Directory** to where your custom action
plugins live, and load them. Your actions then appear in the Sequencer Assets panel's
Actions section, sorted after the built-ins and marked with a **wrench icon**, labeled with
the display name from the Custom Action Definition.

A **Bind Targets** section appears below the standard properties **only when the action has
an animated value type** — Float, Double, Vector2, Vector3, Vector4, Quaternion, or
Transform, shown after a colon in the section header. Each binding card has a Component
dropdown (Transform, Opacity, Billboard, Model — filtered to what the value type supports)
and an Entity dropdown whose scope depends on the component:

| Component | Entity scope |
| --- | --- |
| Transform | Locked to the track's own entity — no subtree choice |
| Billboard, Opacity | Every descendant of the track's entity |
| Model | Descendants, plus a **Value** dropdown filtering to bindable material parameters |

**`+ Add Binding`** adds a card seeded with the first available component and entity; the
minus button removes one. A missing component produces a validation row with an inline add
button — the same pattern as Play Audio and Billboard Blend.

## Motion Path

Dragging a Motion Path action onto a track immediately creates a **default two-point
straight line**, with diamond markers above the path in the viewport.

Selecting it reveals a viewport toolbar with Move / Rotate / Scale gizmos (**W / E / R**)
operating on the selected point.

**Four ways to add a point:**

1. Double-click along the path line in the viewport — divides that segment at the click.
2. Double-click the point bar in the Inspector's timeline — inserts at a specific *time*
   rather than a specific position.
3. With the **last** point selected, click anywhere in 3D space — extends the path there.
   This is how you build a path out point by point.
4. Select the last point, then click the **first** point — closes the path into a loop.

Each point carries **Position, Rotation ZYX, Scale, Time, and Ease Type** (Linear for
constant speed, Ease In/Out variants to slow into or out of a point).

**Shape** generates a path instead of hand-placing it:

| Shape | Behavior |
| --- | --- |
| **Custom** *(default)* | Manual, point by point |
| **Orbit** | Circular/elliptical. Parameters: **Radius**, **Number of Points** (minimum 4), **Spins Per Orbit** (full 360° self-rotations per orbit), **Spin Axis** |
| **Spin** | Rotates in place around a central point rather than traveling a loop |

Shape-independent toggles: **Look Along Path** (orient to direction of travel), **Closed
Shape** (connect end to start), **Constant Speed** (uniform rate regardless of uneven point
timing).

## Cross-fades — the 0.75 second ceiling

Overlapping clips cross-fade, but **only up to 0.75 seconds**. Under it, the Sequencer draws
a darker rounded region with a cross-fade icon. Past it, the indicator becomes a **warning**
and the cross-fade is reported as **"Disabled"**. If you see that warning the transition is
not blending at all — shorten the overlap, don't assume it degrades gracefully.

## Wiring a Sequence for auto-play

With the Root Entity rule satisfied, everything happens in the Animation Library
Component's Inspector panel:

1. Click **Add Animation Entry** (the **`+`** at the bottom of the component). A new entry
   appears named "Empty."
2. Open the entry's dropdown on the right. It lists **both** animation clips embedded in the
   entity's USD asset **and** any Sequences rooted at this entity or its prototype, side by
   side. Selecting your Sequence renames the entry to match; double-click the name to rename
   it manually later.
3. **The Auto Play toggle only appears once at least one entry has an assigned animation** —
   before that there is nothing to auto-play, so it's hidden entirely.
4. Turn Auto Play on. A **Default Animation** dropdown appears; choose which entry plays when
   the entity is added to the scene and enabled.

No script is needed to start playback. At runtime the same entries are reachable through
`AnimationLibraryComponent` — **Auto Play just means RealityKit makes that call for you.**

## Known gaps in Apple's own docs

Two articles referenced from these pages are **not published**:
`automating-motion-path-creation-with-editor-scripting-commands` (building a Motion Path
programmatically) and `NavigationMeshLayers`. Both 404 as of this fetch. Editor scripting
commands are clearly real — the auto-play article names
`edit_entry_in_animation_library_component` — but their reference isn't up yet.
