// mv_amplify.js — true datamosh via ffedit: multiply every forward motion vector
// so motion DRAGS and the smear propagates down the GOP instead of healing.
// Run:  ffedit -i glitchready.m2v -s mv_amplify.js -sp 3 -o moshed.m2v
// -sp <factor> sets the amplification (INTEGER only — ffedit's -sp rejects floats;
// the 2.5 default below is fine as an in-script literal). Higher = meltier.
let factor = 2.5;

export function setup(args) {
  args.features = ["mv"];
  if ("params" in args) factor = args.params;
}

export function glitch_frame(frame) {
  const fwd = frame.mv?.forward;        // undefined on intra (keyframe) frames
  if (!fwd) return;
  frame.mv.overflow = "truncate";       // clamp instead of wrapping on overshoot
  fwd.mul(MV(factor, factor));          // exaggerate every block's motion
}
