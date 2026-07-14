---
topic_id: "v2:LPJF"
topic_path: "metal-renderer/passthrough-rendering"
semantic_id: "7Pc2djsPy7V_9hRm3Gq4NrjqA4_2AAAI"
related_ids:
  - "nvOnDK5IQrfJlB40VHmytfiIEotAsAAF"
  - "3vc2au8qe7-q5zKtwpVQttjKAQGKMAAP"
---
# Shared-encoder texture-slot clobber across the per-eye loop (the "only the right eye is wrong" tell)

Source (the bug this generalises):

- `ios/KaraokeVR/StereoARRenderer.swift` — camera Y/CbCr bound ONCE before the eye loop
  (`encoder.setFragmentTexture(texY, index: 0)` / `texCbCr, index: 1`), then `drawTrailComposite`
  binds the trail buffer at `setFragmentTexture(trailTex, index: 0)` mid-loop. Fixed at commit on
  branch `main`, 2026-06-28 (mode-4 depth-reprojected stereo).
- Apple: a `MTLRenderCommandEncoder`'s argument table (textures/buffers/bytes) is **persistent
  state** — a binding stays until overwritten or the encoder ends.
  <https://developer.apple.com/documentation/metal/mtlrendercommandencoder>

## The shape of the bug

The renderer draws both eyes in ONE encoder: `for (index, eye) in eyes.enumerated()`. Resources
that are the same for both eyes (the camera Y/CbCr planes) are bound ONCE, before the loop, to
save redundant binds. That's correct — UNTIL some draw _inside_ the loop binds a different texture
to one of those same slots. The argument table is sticky, so:

- **Eye 0 (left)** draws its backdrop while slot 0 still holds the camera Y plane → correct.
- A later draw in eye 0's body (`drawTrailComposite`) binds `trailTex` to slot 0.
- **Eye 1 (right)** re-runs the _same_ backdrop code, which still assumes slot 0 = camera Y, but
  slot 0 now holds `trailTex` → the right eye samples the wrong texture.

Next frame the pre-loop rebind cleans slot 0 again, so it's **the right eye, every frame** — the
left eye never shows it because it always runs before the clobber.

## The tell

"**Only the second (right) eye is wrong, and it looks like some _other_ pass's buffer**" (here the
mode-4 comet trail read as luma → inverted + ghost-tripled). When one eye is fine and the other is
broken in a shared-encoder per-eye loop, suspect a sticky argument-table slot clobbered by a
mid-loop draw **before** you suspect per-eye math (eyeView sign, lensShift, viewport, UV halves) —
that math is usually symmetric and would break BOTH eyes, not one.

## Diagnosis recipe

1. `grep -n "setFragmentTexture\|setVertexTexture\|setFragmentBytes\|setVertexBuffer"` the renderer.
2. List which indices are bound ONCE before the eye loop (relied on by every eye) vs. which are
   (re)bound inside each per-eye draw.
3. Any pre-loop slot that a mid-loop helper also writes is a clobber that breaks the eye(s) after
   the helper runs. (Here: camera planes at fragment 0/1 pre-loop; `drawTrailComposite` writes 0.)

## Fixes (cheapest first)

- **Restore the slot right after the offending draw** (used here): re-bind `texY` to fragment
  index 0 after `drawTrailComposite`. Minimal, scoped to the one mode.
- **Rebind the shared resources at the top of each eye iteration** instead of once before the loop
  — robust to any future mid-loop clobber, at the cost of one redundant bind per eye.
- **Give transient passes their own non-shared slot** (e.g. composite samples a slot no per-eye
  backdrop relies on). Watch for collisions: in this renderer 0/1 = camera, 2 = depth, 3 = lyric/
  menu plate, so a "free" index is scarce — prefer one of the rebind options.
