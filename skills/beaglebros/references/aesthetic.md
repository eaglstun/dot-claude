# The Beagle Bros look

The visual identity: a 19th-century mail-order catalog that somehow sells disk
utilities. Ornate, hand-made, friendly, a little absurd. Here's how to evoke it.

## Core visual vocabulary

- **Victorian / Edwardian woodcut engravings** — top hats, handlebar mustaches, frock
  coats, pointing hands, disembodied gloved hands holding objects, ornate filigree,
  scrollwork banners, "patent medicine" energy. Black-on-cream, high-contrast line art.
- **The manicule ☞** (the little pointing hand) as a bullet / "look here" marker.
- **Ornamental rules and borders** — double rules, corner flourishes, banner ribbons
  carrying the title.
- **Old display typefaces** — fat slab serifs, condensed Victorian poster faces, drop
  shadows. For digital text, an ALL-CAPS slab headline reads "old catalog" instantly.
- **Exuberant catalog copy** under each item ("Behold! UTILITY CITY — 21 programs!").
- **Cream/parchment background, single spot color** (deep red or blue) for accents.

## Generating clip art

If you want to generate the engravings, look for a skill (or tool) that calls an
image-generation service — something local like **Draw Things**, or a hosted one like
**Replicate**, **Pollinations**, **fal**, **Stability**, etc. Use whichever is already
installed; this skill doesn't ship one. No image tool around? Hand the prompt below to
the user to run wherever they like. Prompt skeleton that lands the look:

> "Victorian engraving, 19th-century woodcut illustration, vintage patent-medicine
> advertisement style, a [SUBJECT] in a top hat, fine cross-hatching, black ink line
> art on aged cream paper, ornate decorative border, high contrast, antique catalog
> clip art" — negative: "color, photo, modern, gradient, 3D render"

Swap [SUBJECT] for the thing your project is about (a beagle in a top hat operating a
floppy drive is, frankly, the canonical move). FLUX or SDXL handle engraving style well.

## ASCII tip-card template (for READMEs, CLIs, comments)

The famous "Peeks & Pokes"-style tip card, rendered in plain text:

```
,--------------------------------------------------------.
|  ☞  B E A G L E   B R O S   T I P   # 7                 |
|--------------------------------------------------------|
|                                                        |
|   Press [TAB] to autocomplete a half-typed command.    |
|   Your fingers will thank you. Your wrists, eventually. |
|                                                        |
|   (Works anywhere you see the > prompt.)               |
|                                                        |
`--------------------------------------------------------'
```

Simpler inline manicule tip, for docs:

```
☞  Pro tip: pipe it through `less` and the 4,000-line output stops bullying you.
```

Banner / splash header for a CLI start screen:

```
 ===========================================================
   ★  W I D G E T R O N   3 0 0 0  ★   "It just widgets."
       Beagle-Bros-approved · No quarters required
 ===========================================================
```

## Where this belongs (and where it doesn't)

- **Good fits:** READMEs, landing pages, splash screens, an `about`/`--version` easter
  egg, release-note headers, a printable tip card, a retro-themed site section — anywhere
  a project already leans retro/print and wants the engraving energy.
- **Hold back on:** dense reference tables, API docs, anything where ornament fights
  scannability. Beagle Bros put the cartoons in the _margins_ — the technical content
  stayed clean. Keep the engravings out of the load-bearing data.
