# Gotchas & fine print

The always-hit rules (inspect first, container limits, the `MV(x,y)` write rule, the
broken prep-script flags) live in SKILL.md. These are the rest, all verified on this
install (macOS aarch64 v0.10.2).

- **The grid is `forward[y][x]`** — row-major, `[mb_row][mb_col]`. `.width` is columns,
  `.height` is rows. MVs are `[horizontal, vertical]` in **half-pel** units.
- **Deep-copy before you mutate** if you're accumulating across frames — use
  `mvs.dup()`, not a reference.
- **`frame.mv.overflow = "truncate"`** before MV math that can overshoot the
  codec's legal range.
- **Don't touch `pkt_pos`/`pts`/`dts`** in exported JSON — informational; editing
  them corrupts muxing.
- **Python scripts** need `FFGLITCH_LIBPYTHON_PATH` + numpy — working combo in
  scripting.md.
- **`-sp` rejects floats** — pass ints, or a JSON string and parse it.
- The binaries print enormous help (`-h`). The website docs at
  <https://ffglitch.org/docs/0.10.2/> are the real manual, but many field names
  literally render as "TODO" — this skill's references fill those gaps from
  verified experiments.
