// DC-coefficient streaks — adds a large constant to the luma DC coefficient in
// a vertical band of 8x8 blocks. On P-frames only deltas are coded, so the
// brightness error smears and drags across the GOP: hard vertical scars.
// Verified against FFglitch 0.10.2 (MPEG-2; also works on JPEG/MJPEG q_dc).
//
//   ffedit -i in.m2v -s dc_streak.js -y -o out.m2v
//   ffedit -i in.m2v -s dc_streak.js -sp 400 -y -o out.m2v   # harsher
//
// frame.q_dc.data is [plane][block_row][block_col] — plane 0 = luma (Y),
// 1/2 = chroma (Cb/Cr). Cells are plain numbers; null/undefined = not coded
// on this frame (skip those). Grid is one cell per 8x8 block, NOT per
// macroblock: a 320x240 frame gives a 40x30 luma grid.

let boost = 200;
const bandStart = 10; // first block column of the streak
const bandWidth = 4; // streak width in blocks

export function setup(args) {
  args.features = ["q_dc"];
  if ("params" in args) boost = args.params;
}

export function glitch_frame(frame) {
  const planes = frame.q_dc?.data;
  if (!planes) return;
  const luma = planes[0];
  for (let y = 0; y < luma.length; y++) {
    const row = luma[y];
    for (let x = bandStart; x < bandStart + bandWidth && x < row.length; x++) {
      if (row[x] !== null && row[x] !== undefined) row[x] += boost;
    }
  }
}
