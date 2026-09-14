// mv_drift.js — push every forward motion vector by a constant offset.
// The whole picture "slides" in one direction and smears as it does.
//
//   ffedit -i ready.m2v -s mv_drift.js -sp 16 -o out.m2v
//   (or)  ffglitch.py script ready.m2v mv_drift.js -o out.m2v --sp 16
//
// -sp sets the horizontal push (default 12). Read cells as c[0]/c[1];
// WRITE them with MV(x, y) — assigning a plain [x,y] array throws.

let push = 12;

export function setup(args) {
    args.features = [ "mv" ];
    if ("params" in args) push = args.params;
}

export function glitch_frame(frame) {
    const fwd = frame.mv?.forward;          // 2-D grid [row][col]; undefined on intra frames
    if (!fwd) return;
    frame.mv.overflow = "truncate";         // clamp values that exceed the codec range

    for (let y = 0; y < fwd.length; y++) {
        for (let x = 0; x < fwd[y].length; x++) {
            const c = fwd[y][x];            // an MV object (index with c[0], c[1]) or null
            if (c) fwd[y][x] = MV(c[0] + push, c[1]);
        }
    }
}
