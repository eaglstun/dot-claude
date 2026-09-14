// Sine-wave motion warp — rows of macroblocks shear left/right on a traveling
// sine wave. Because P-frames compound down the GOP, the ripples accumulate
// into a liquid, melting drift. Verified against FFglitch 0.10.2.
//
//   ffedit -i in.m2v -s mv_sine.js -y -o out.m2v
//   ffedit -i in.m2v -s mv_sine.js -sp 12 -y -o out.m2v   # stronger (amplitude)
//
// Knobs: amplitude (px per frame), wavelength (rows per cycle), speed.

let amplitude = 6;
const wavelength = 3; // macroblock rows per sine cycle
const speed = 5; // frames per phase step
let n = 0;

export function setup(args) {
  args.features = ["mv"];
  if ("params" in args) amplitude = args.params;
}

export function glitch_frame(frame) {
  const fwd = frame.mv?.forward;
  if (!fwd) {
    n++;
    return;
  }
  frame.mv.overflow = "truncate";
  for (let y = 0; y < fwd.height; y++) {
    const shear = Math.lround(amplitude * Math.sin(y / wavelength + n / speed));
    for (let x = 0; x < fwd.width; x++) {
      const c = fwd[y][x];
      if (!c) continue; // skipped block
      fwd[y][x] = MV(c[0] + shear, c[1]);
    }
  }
  n++;
}
