# CLI control battery — results (2026-06-01)

Re-ran every control that failed over the **HTTP API** through **`draw-things-cli`**
(native engine, `--config-json` with the same `controls` array). Reference images:
fox = seated red fox photo, pose = standing human, face = red-haired freckled portrait.
Each output PNG is in this directory.

| Control         | File / family                                 | HTTP API   | CLI (native)                                                                                 | Output                  |
| --------------- | --------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------- | ----------------------- |
| Depth           | `controlnet_depth_1.x` (SD)                   | ✅ works   | ✅ works (sanity check — fox pose transferred)                                               | `cli_depth.png`         |
| OpenPose        | `controlnet_openpose_2.x` (SD)                | ❌ generic | ❌ **confirmed no-op** — byte-identical across standing/sitting/none (A/B below)             | `cli_openpose.png`      |
| Union Pro 2.0   | `controlnet_union_pro_flux…` (FLUX)           | ❌         | ❌ still no structure transfer from a raw photo (36 s, heavy, but generic robot)             | `cli_unionpro.png`      |
| Redux           | `flux_1_redux` (FLUX)                         | ❌ ignored | ❌ **confirmed no-op** — output byte-identical with/without the control (A/B below)          | `cli_redux.png`         |
| Alimama Inpaint | `controlnet_alimama_inpaint_flux…` (FLUX)     | ❌ garbled | ⚠ coherent (vs HTTP garbage) but **did NOT preserve the unmasked region** — not true inpaint | `cli_alimama.png`       |
| Kolors pose     | `controlnet_pose_kwai_kolors` (Kolors)        | ❌         | ❌ close-up bust, no pose transfer                                                           | `cli_kolors_pose.png`   |
| Kolors FaceID   | `ip_adapter_faceid_plus_kwai_kolors` (Kolors) | ❌         | ❌ identity not transferred (unrelated face)                                                 | `cli_kolors_faceid.png` |

## Takeaways

- **Byte-level A/B is the only honest test.** Two controls I called "working/improved"
  from a single image (Redux, OpenPose) turned out **byte-identical with/without the
  control** — total no-ops. Eyeballing a plausible result is not evidence.
- **The "heavy run-time = control working" heuristic was wrong** — the no-control baseline
  also took ~28–30 s. Run-time is just the model's gen speed.
- **Only two controls are genuinely verified (visible, reference-dependent effect):**
  **Depth** (SD) and **PuLID** identity (FLUX). _(Both shown by strong visible effects;
  not yet byte-A/B'd — see follow-ups.)_
- **No-op / non-functional over both interfaces:** OpenPose, Kolors pose, Kolors FaceID,
  Union Pro, Redux (no-ops or no transfer), and Alimama Inpaint (coherent but ignores the
  mask — regenerates the whole frame).
- **Mechanism:** the CLI takes the same `controls` array via `--config-json`; structural
  guides go in `--image` (img2img, `--strength 1.0`); identity references go in
  `controls[].image` (base64).

## Redux A/B (the lesson on not trusting eyeballs)

Fixed seed 7, prompt "a photo", FLUX.1-dev. Files `redux_ab_1..4`:

| #   | Setup                                     | md5                       |
| --- | ----------------------------------------- | ------------------------- |
| 1   | txt2img, no image, no control (pure seed) | `cb9c…`                   |
| 2   | img2img fox, **no** Redux                 | `4889…`                   |
| 3   | img2img fox **+ Redux**                   | `4889…` ← identical to #2 |
| 4   | Redux + redhead reference                 | `e475…`                   |

**#2 == #3 byte-for-byte** → adding the Redux control changed nothing. The antlered-woman
composition is **seed 7's output** (it appears in #1, with no reference at all) — the fox
never shaped it. The `--image` input causes faint pixel changes (#2 ≠ #4), i.e. plain
img2img has a small effect, but Redux contributes none of it. My original
"thematic variation of the fox" claim was pattern-matching onto a coincidence.

## OpenPose A/B — confirmed no-op

Fixed seed 7, prompt "a chrome humanoid robot, full body", SD 1.5. Files `op_ab_1..4`:

| #   | Setup                                | md5     |
| --- | ------------------------------------ | ------- |
| 1   | txt2img, no image, no control        | `f683…` |
| 2   | img2img standing ref, **no** control | `f683…` |
| 3   | OpenPose + standing ref              | `f683…` |
| 4   | OpenPose + **sitting** ref           | `f683…` |

**All four byte-identical.** OpenPose changed nothing, and swapping a standing ref for a
cross-legged sitting ref changed nothing. Confirmed no-op (like Redux).

## Inpaint preservation check — fails

`inpaint_preserve.png`: fox with the right third alpha-masked, prompt "a snowman". The
output is a full snowman scene with **no fox in the unmasked left region** — it
regenerated the whole frame instead of inpainting the masked area. Not functioning as
inpaint; the coherent-vs-HTTP-garbage difference is real but the control's contribution
over a plain prompt is unproven.

**Cheap fix attempt (`cli_inpaint_preserve2.png`):** added
`configuration.preserveOriginalAfterInpaint: true` (the flag `edit-background.js` sets) to
the `--config-json`. The flag **was honored** (output changed — different md5 from the
no-flag run), but the result is **still a full snowman with no fox preserved**. Reason:
there's nothing to preserve without a **mask**, and the CLI has no mask input — no
`--mask` flag, and the `--image` alpha channel isn't read as one. The mask is **canvas
state** (`canvas.loadMaskFromSrc` in the scripting API), unreachable from the CLI. So
config-only fixes can't deliver regional inpaint; it needs in-app Scripts or (likely) gRPC.

## Open follow-ups

- **Depth & PuLID still need the byte-level A/B** to earn their ✅ — they show strong
  visible reference-dependent effects (robot took the fox's pose; freckled face carried
  into a new style), which a no-op can't produce, but they haven't had the formal test.
- Union Pro: try feeding an **already-extracted** depth/edge map instead of a raw photo.

## How these were generated

`draw-things-cli generate --model <m> --prompt <p> [--image <ref> --strength 1.0]
--config-json '{"controls":[{…full struct…}]}' --output <file>` — see
[`../references/controlnet.md`](../references/controlnet.md) for the full struct and the
two image-delivery mechanisms.
