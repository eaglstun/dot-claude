---
topic_id: "v2:DGAP"
topic_path: "model-runners/gen-3d-contracts"
semantic_id: "VusYKdzX9A-tRfJ9Nx7iVklHZvAuUAAL"
related_ids:
  - "Xk0bvdbWEkcN1WJodG5DB2NydLaMMAAO"
  - "XnxTGf_GEgctzVJodntHVXF0dbSEEAAB"
---
# Generation cost + commercial-license picture (Tripo & Meshy)

The "report cost + license" half of the agent remit, in one place: per-operation credit costs, the
subscription tiers, and — the part that actually gates shipping — the **commercial-use / IP terms**
for AI-generated 3D assets, tied to the API tier the key is on. This app **ships under the LLC
(commercial)**, so a free-tier asset's CC BY 4.0 attribution obligation is a real blocker, not a
footnote.

**Grounded in each vendor's live pricing pages** (`tripo3d.ai/pricing`, `meshy.ai/pricing`,
`docs.meshy.ai/en/api/pricing`, read 2026-06-29). The pricing/marketing pages render enough for
WebFetch; the **dedicated legal/terms-of-service pages are SPAs/moved and did NOT load** (Meshy
`docs.meshy.ai/en/legal/*` returned 404; Tripo's ToS not separately fetched) — so the **license
wording below is quoted from the pricing pages**, which state it inline. For a contract-grade read
before a high-stakes release, open the ToS in a browser. **Verify live before relying on a tier
claim** (per CLAUDE.md — these change).

## The rule that matters: free tier = CC BY 4.0 = attribution debt

Both vendors gate commercial ownership behind a **paid** tier and put the **free** tier under
**CC BY 4.0** (Creative Commons, commercial use allowed but **attribution required**). So:

- **If the key is on a free tier**, anything you generate carries an **attribution obligation** and
  the model is **public** (Tripo explicitly: "Public models (CC BY 4.0)"). Flag this before the
  asset goes into a shipped or ReplayKit-recorded karaoke take. Don't silently ship it.
- **If the key is on any paid tier**, the asset is **private + commercially yours** (Tripo) /
  **fully owned** (Meshy) — no attribution. This is the state you want for a shipped take.
- **Don't assume the tier — check or ask.** Tripo: `GET /user/balance` confirms there's credit but
  not the plan; ask the user which plan the key is on if it's not obvious. Meshy: `consumed_credits`
  is per-task; tier likewise needs confirming.

## Tripo3D

### Tiers (from `tripo3d.ai/pricing`, read 2026-06-29)

| Plan     | Price (50%-off annual / standard mo.) | Monthly credits | License                                    |
| -------- | ------------------------------------- | --------------- | ------------------------------------------ |
| **Free** | $0                                    | 200 (~8 models) | **Public models (CC BY 4.0)** — attrib req |
| **Pro**  | $13.93 / $19.90                       | 3,000 (~120)    | **Private models & commercial use**        |
| **Max**  | $53.94 / $89.90                       | 25,000 (~1,000) | Private models & commercial use            |
| **Team** | $54.93 / $109.90 per seat             | 45,000 (~1,800) | Private models & commercial use            |

### Per-operation cost (credits)

The pricing page doesn't itemize API ops; anchors from the research (`rig-and-animate-apis.md`,
verify live): **rig ~25cr (~$0.25)** · **retarget ~10cr (~$0.10)** · generation varies by
`model_version`. Check `GET /user/balance` (`{data:{balance,frozen}}`) before a batch. Credits map
to dollars only via the plan's bundle (e.g. Pro $19.90 → 3,000cr ≈ $0.0066/cr standard); there's no
published per-credit à-la-carte rate on the page read.

## Meshy

### Tiers (from `meshy.ai/pricing`, read 2026-06-29)

| Plan           | Price/mo | Monthly credits | License / ownership                                        |
| -------------- | -------- | --------------- | ---------------------------------------------------------- |
| **Free**       | $0       | 100             | **CC BY 4.0** — "we grant you a CC BY 4.0 license"; attrib |
| **Pro**        | $20      | 1,000           | **Full ownership** — "you own all assets you create"       |
| **Studio**     | $60      | not specified   | Full ownership; "exclusive" rights to distribute and sell  |
| **Enterprise** | custom   | custom          | Full ownership; custom terms                               |

Quoted wording from the pricing page: free → _"we grant you a CC BY 4.0 license instead"_; paid →
_"If you are on a premium plan, you own all assets you create with Meshy"_ with _"full rights to
distribute and sell."_ Additional credits are purchasable on Pro/Studio.

### Per-operation cost (credits, from `docs.meshy.ai/en/api/pricing`, read 2026-06-29)

| Operation              | Credits                                              |
| ---------------------- | ---------------------------------------------------- |
| Text-to-3D **preview** | 5 (meshy-6 / low-poly: **20**)                       |
| Text-to-3D **refine**  | 10 per texture task                                  |
| Image-to-3D            | meshy-6/low-poly 20 (no tex) / 30 (tex); else 5 / 15 |
| **Auto-rigging**       | **5**                                                |
| **Animation**          | **3**                                                |

No credit→dollar exchange rate is published on the docs page (buy credits via subscription).
`consumed_credits` is returned on each task object. Meshy is the **cheaper rig+animate** path
(rig 5cr + anim 3cr = 8cr vs Tripo ~35cr for rig+retarget).

## Cost discipline (agent behavior)

- **One good asset per request** unless asked to iterate — don't fan out dozens of speculative
  generations. The expensive steps are generation/refine; rig+animate are cheap on both vendors.
- **Report credits/$ spent** in the return message (Tripo: balance delta or known op anchors;
  Meshy: sum of `consumed_credits`).
- **Decimate before rigging** (Tripo `highpoly_to_lowpoly`, Meshy `target_polycount`/`lowpoly`) so
  you're not paying to rig + ship a needlessly heavy mesh on a phone GPU.

## License decision table (what to put in the return message)

| Key's tier            | Asset license         | Ships in a recorded take?          |
| --------------------- | --------------------- | ---------------------------------- |
| Tripo Free            | CC BY 4.0, **public** | Only with **attribution**; flag it |
| Tripo Pro/Max/Team    | Private + commercial  | Yes, clean                         |
| Meshy Free            | CC BY 4.0             | Only with **attribution**; flag it |
| Meshy Pro/Studio/Ent. | Full ownership        | Yes, clean                         |

Always state, per produced asset: **vendor + tier + resulting license + credits spent** — and if
free-tier, the **attribution string** the take must carry.

## Sources

- `tripo3d.ai/pricing` — Tripo tiers, prices, monthly credits, "Public models (CC BY 4.0)" vs
  "Private models & commercial use" (read 2026-06-29).
- `meshy.ai/pricing` — Meshy tiers, prices, credits, CC BY 4.0 (free) vs full ownership (paid)
  wording (read 2026-06-29).
- `docs.meshy.ai/en/api/pricing` — Meshy per-operation credit costs (read 2026-06-29).
- Op-cost anchors for Tripo: `rig-and-animate-apis.md` / `tripo-api.md` (2026-06-28 research; not
  re-confirmed against a Tripo per-op price page, which doesn't itemize API ops).
- **Could not fetch:** Meshy dedicated legal pages `docs.meshy.ai/en/legal/{terms-of-service,
commercial-use}` (HTTP 404 — likely moved/SPA); Tripo Terms of Service page (not separately
  loaded). License wording above is from the pricing pages, which state it inline; open the ToS in a
  browser for a contract-grade read before a high-stakes release.
- Companions: `tripo-api.md` · `meshy-api.md` (the `consumed_credits`/`balance` fields these costs
  attach to).
