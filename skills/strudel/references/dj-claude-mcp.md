# dj-claude MCP

The `dj-claude` MCP server (configured in `.mcp.json` as `yarn dj-claude-mcp`) plays
Strudel patterns through an audio backend without you touching the browser. Tools appear as
`mcp__dj-claude__*`.

**Key fact:** every generative tool works **without an `ANTHROPIC_API_KEY`** as long as you
pass Strudel code directly via the `code` / `layers` / `stages_code` params. The `prompt` /
`directive` params (AI-generated music) are what require the key. Since you write Strudel
yourself, prefer the direct-code path. The server also exposes a `strudel://reference` and
`strudel://roles` MCP resource you can read for syntax.

## Audio backends

`switch_audio` toggles between **Node** (terminal audio) and **Browser** (opens a tab,
higher quality). Node mode is the zero-setup default.

## Tools

### Playback — single pattern

- **`play_strudel`** `{ code }` — evaluate raw Strudel code directly. The bread-and-butter
  tool: no key needed, you control exactly what plays.
- **`play_music`** `{ code | prompt }` — same as above but `prompt` routes through Claude
  (needs key). Use `play_strudel` unless you specifically want AI generation.
- **`set_vibe`** `{ mood }` — instant built-in pattern for a mood. Moods: `chill`, `dark`,
  `dreamy`, `epic`, `focus`, `funky`, `hype`, `weird`. No key needed.
- **`play_preset`** `{ name? }` — play from the curated library; call with no args to list
  presets. No key needed.
- **`hush`** — stop all playback immediately.
- **`now_playing`** — show current code + commentary.

### Layered jam (compose with `stack()`)

- **`jam`** `{ role, code | prompt }` — add/update one layer by role (`drums`, `bass`,
  `melody`, `pads`, `chords`, `lead`, …). Layers compose via `stack()`.
- **`jam_preview`** `{ role, code }` — generate/preview a layer **without** playing/storing it.
- **`jam_status`** — list active layers and their code.
- **`jam_clear`** `{ role? }` — remove one role, or all layers if omitted.
- **`mix_analysis`** — analyze octave ranges, effects, gain, frequency-band occupancy across
  layers; returns mix suggestions. No key needed.

### Full-band orchestration

- **`conduct`** `{ layers | directive }` — generate a whole band at once. `layers` is a map
  of `role -> Strudel code` (no key). Matches band templates (jazz combo, rock, electronic,
  ambient) or custom roles.
- **`conduct_evolve`** `{ layers | directive }` — evolve all active layers; pass a `layers`
  map for a single-pass update (no key), or `directive` for AI multi-stage evolution.
- **`live_mix`** `{ stages_code[] | prompt }` — autonomous DJ set, ~20s between stages.
  `stages_code` is an array of Strudel strings, one per stage (no key).

### Session state

- **`set_context`** `{ … }` — tell DJ Claude what you're working on so generated music adapts.
- **`snapshot_save` / `snapshot_load` / `snapshot_list`** `{ name }` — save/restore named mixes.
- **`export_code`** — export current composed code with header comments.

## Typical flows

**Just play something I wrote:**

```text
play_strudel  code = stack(sound("bd*4"), sound("hh*8").gain(.6)).slow(2)
```

**Build a jam layer by layer:**

```text
jam  role=drums  code = sound("bd*4, ~ sd ~ sd, hh*8")
jam  role=bass   code = note("c2 eb2 g2 bb1").sound("sawtooth").lpf(700)
jam_status            # see what's stacked
mix_analysis          # check for frequency clashes
jam_clear role=bass   # drop a layer
```

**Whole band in one call:**

```text
conduct  layers = { drums: 'sound("bd*4, hh*8")',
                    bass:  'note("c2 g2").sound("sawtooth")',
                    keys:  'note("<c4,e4,g4>").sound("piano").room(.4)' }
```

Note: this project's `index.js` browser path and the MCP are independent ways to play —
the MCP doesn't read `index.js`. Use `play_strudel` to audition snippets, then paste the
winners into `index.js` for the click-to-play browser experience.
