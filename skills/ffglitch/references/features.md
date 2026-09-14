# ffedit features & JSON format

## What "features" are

A _feature_ is a category of codec data `ffedit` can decode, expose, and rewrite. You
pick them with `-f` on the CLI or `args.features = [...]` in a script. **Which features
exist depends entirely on the file's codec** — so always start with:

```bash
ffedit -i input.m2v        # no -o: prints the features supported for this file
```

Select one with `-f mv`, or target a specific stream with `-f mv:0` (feature `mv`,
stream 0). Without `-f`/`features`, export/apply covers _all_ supported features.

## Feature names by codec (verified against v0.10.2)

These are the **exact** feature lists `ffedit -i` printed for files this skill
generated. Names are real (`q_dct`, not `dct`); always reconfirm with `ffedit -i file`.

**MPEG-2 video** (raw `.m2v` elementary stream) — the richest set:

| feature       | data                                                                   |
| ------------- | ---------------------------------------------------------------------- |
| `info`        | frame info: `pict_type`, `interlaced`, `mb_type` map (read-only intel) |
| `mv`          | **motion vectors** (the headline glitch)                               |
| `mv_delta`    | motion vectors (delta only)                                            |
| `q_dct`       | quantized DCT coefficients (all 64/block)                              |
| `q_dct_delta` | quantized DCT coefficients (with DC delta)                             |
| `q_dc`        | quantized DCT coefficients (DC only)                                   |
| `q_dc_delta`  | quantized DCT coefficients (DC delta only)                             |
| `qscale`      | quantization scale (per slice)                                         |
| `mb`          | macroblock (raw coded bits + sizes)                                    |

**MPEG-4 part 2** (in `.avi`): `info`, `mv`, `mv_delta`, `mb`, `gmc` (global motion
compensation). No `q_*`/`qscale` here.

**JPEG / MJPEG** (single `.jpg` or MJPEG in `.avi` — identical list, codec is
"MJPEG (Motion JPEG)" either way): `info`, `q_dct`, `q_dct_delta`, `q_dc`,
`q_dc_delta`, `dqt` (quantization table), `dht` (huffman table). No motion —
JPEG glitching is all coefficients and tables.

**PNG / APNG** (0.10.1+): `headers` (incl. APNG `fcTL` chunk objects with
`dispose_op`/`blend_op`), `idat` (image data — `frame.idat.rows`, where `row[0]`
is the per-row filter_type byte; rewrite it to corrupt prediction).

That's the complete supported list — JPEG, MPEG-2, MPEG-4, PNG (docs). H.264/H.265
in MP4 expose nothing — prep with `ffgac` into one of the above first (see
ffgac-prep.md). Containers: only `rawvideo`, AVI, MOV/MP4; MKV is rejected. No
audio glitching (audio in AVI/MOV passes through in sync).

## Export → edit → apply

```bash
ffedit -i in.m2v -f mv -e data.json          # export motion vectors
#   edit data.json ...
ffedit -i in.m2v -f mv -a data.json -o out.m2v   # apply back (same -f selection)
```

Use the **same `-f` selection** on export and apply. Apply only rewrites the features
present in the JSON.

## Top-level JSON structure

```jsonc
{
  "ffedit_version": "...",
  "filename": "in.m2v",
  "sha1sum": "...",
  "features": ["mv"],
  "streams": [
    {
      "codec": "mpeg2video",
      "frames": [
        {
          "pkt_pos": 12345, // byte offset — INFORMATIONAL, do not edit
          "pts": 0, // INFORMATIONAL, do not edit
          "dts": 0, // INFORMATIONAL, do not edit
          "mv": {
            /* the selected feature's object — see shapes below */
          },
        },
        // ...one object per frame...
      ],
    },
  ],
}
```

## Per-feature data shapes (all verified on v0.10.2 exports)

The same shapes appear live on `frame.<feature>` in script mode.

### `mv`

```jsonc
"mv": {
  "forward":  [ /* [mb_row][mb_col] grid of [h,v] pairs, or null cells */ ],
  "backward": [ /* present on B-frames only */ ],
  "fcode": [2, 2],      // codec MV range/precision — informational
  "overflow": "warn"    // "assert" | "truncate" (recommended) | "ignore" | "warn" (default)
}
```

Grid is one cell per **16x16 macroblock**: 320x240 → 20 cols × 15 rows. Intra
frames have no `forward`. Note: ffmpeg's mpeg2 encoder defaults to **no B-frames**,
so preps won't have `backward` unless you add `-bf 2`.

Values are in **half-pel units** (an MV of `[2,0]` moves ~1 pixel right). Legal
range from `fcode` (docs): MPEG-2 `±(1<<(3+fcode))`, MPEG-4 `±(1<<(4+fcode))`
(max is one less) — hence prepping with `-fcode 6` for big glitch vectors. On
MPEG-4, a cell may be an Array of **4** MVs (4MV/8x8 mode), each null-or-[h,v].
`mv_delta` is the same shape but delta-coded values. MPEG-4 also exposes `gmc`
(global motion compensation): up to 3 `[x,y]` pairs — officially undocumented
("I don't remember how the gmc calculation is done" — the docs, really).

### `q_dc` / `q_dct`

```jsonc
"q_dc": {
  "data": [ /* [plane][block_row][block_col] — plane 0=Y, 1=Cb, 2=Cr */ ],
  "v_count": [2, 1, 1],  // luma blocks per MB vertically / chroma subsampling
  "h_count": [2, 1, 1]
}
```

Grid is one cell per **8x8 block** (finer than the MV grid): 320x240 → luma 40×30.
`q_dc` cells are single numbers (the DC coefficient); `q_dct` cells are arrays of
up to 64 coefficients (zigzag order, DC first). `null` = block not coded on this
frame — skip, don't invent. On intra frames DC values are large positives
(absolute); on P-frames they're small signed **deltas** — same shape, different
meaning, which is why edits to P-frames smear forward.

On JPEG there's an extra `quant_index` field (which dqt table each plane uses).
JPEG `*_delta` caveat from the docs: "previous DC" follows macroblock raster
scan order, not simply the block to the left. The classic JPEG glitch is one
edit to `q_dc_delta.data[plane][x][y]` — everything after that block in scan
order shifts brightness/color.

### `qscale`

```jsonc
"qscale": { "slice": [ {"0": 2}, {"0": 2}, ... ] }  // one object per slice
```

MPEG-2 has one slice per macroblock row; keys are the starting MB column. Raising
values = crunchier decode of the existing coefficients.

### `info` (read-only intelligence)

```jsonc
"info": {
  "pict_type": "P",        // "I" / "P" / "B"
  "interlaced": false,
  "mb_type": [ /* [row][col] of strings like "I    ", "  cf ", "   f " */ ]
}
```

Use it in scripts to branch on frame type (`frame.info.pict_type`) or find which
blocks are intra/coded/forward. Flags seen in the strings: `I` intra, `c` coded,
`f` forward, `q` quant, `b` backward.

### `mb`

```jsonc
"mb": {
  "data":  [ /* [row] of hex strings — the raw coded macroblock bits */ ],
  "sizes": [ /* [row][col] bit sizes of each macroblock */ ]
}
```

Raw bitstream-level access. Docs: "Macroblocks are mostly self-sufficient, so it
might be possible to reorder them and still have a valid bitstream." Do NOT edit
`sizes` — ffedit uses it to align the bitstream. Expert mode; least-tutorialized
feature; easy to break decode.

### `dqt` (JPEG)

```jsonc
"dqt": { "tables": [ [ /* 64 values, one 8x8 quant table */ ], ... ] }
```

Scaling a table up = blockier, crunchier decode of the same coefficients.
Script access: `frame.dqt.tables[i][j]`; `tables[0][0]` is table 0's DC quant —
the official tutorial's one-line JPEG crush is `frame.dqt.tables[0][0] = 63`.
(`dht`, the huffman table, also exports — the docs themselves say don't touch it.)

## Rules of the road

- **Edit only the feature objects** (`mv`, `q_dc`, …). Leave `pkt_pos`/`pts`/`dts`
  alone — they describe muxing, not picture.
- `null` means that data is absent for that frame/block — skip it, don't invent values.
- Keep array shapes intact. Grids are sized by the frame's macroblock layout; ffedit
  expects matching dimensions on apply.
- For programmatic edits over many frames, **script mode is far better than
  hand-editing JSON** — see scripting.md. The JSON round-trip is best for surgical
  one-off tweaks or feeding another tool. (A `q_dct` export of 4s of 320x240 video
  is already ~8 MB of JSON — it gets big fast.)

## Verifying without changing anything

```bash
ffedit -i in.m2v -o copy.m2v     # "replicate" — proves ffedit can round-trip the file
```

If the replicate fails, the file won't glitch cleanly either; re-encode with `ffgac`.
