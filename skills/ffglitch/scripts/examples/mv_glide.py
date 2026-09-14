# Python glitch script — constant horizontal glide (everything slides right).
# Demonstrates the Python API differences vs JS. Verified on FFglitch 0.10.2.
#
# Python needs BOTH:
#   1. FFGLITCH_LIBPYTHON_PATH pointing at a libpython dylib
#   2. numpy importable in that same interpreter
# On this machine:
#   export FFGLITCH_LIBPYTHON_PATH=$HOME/.pyenv/versions/3.14.2/lib/libpython3.14.dylib
#   ffedit -i in.m2v -s mv_glide.py -y -o out.m2v
#
# Python API differences from JS (all verified):
#   - args is dict-like:      args["features"] = ["mv"]  (not args.features)
#   - frame is dict-like:     frame.get("mv"), mv.get("forward")
#   - forward is a plain list of rows; mutate rows IN PLACE (propagates back)
#   - plain [h, v] list assignment is accepted (no MV() constructor needed)

DRIFT = 8  # pixels per frame, rightward


def setup(args):
    args["features"] = ["mv"]


def glitch_frame(frame, stream):
    mv = frame.get("mv")
    if not mv:
        return
    fwd = mv.get("forward")
    if not fwd:
        return
    for row in fwd:
        for i, cell in enumerate(row):
            if cell is not None:
                row[i] = [cell[0] + DRIFT, cell[1]]
