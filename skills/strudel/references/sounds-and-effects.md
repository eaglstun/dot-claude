# Sounds & effects

How to make a sound, then how to shape it. All effect names are controls — they accept a
value or a mini-notation pattern (`.lpf("400 800")` sweeps per event).

## Sources — where sound comes from

| Source                            | Use                                                                   |
| --------------------------------- | --------------------------------------------------------------------- |
| `sound("bd sd hh")` / `s(…)`      | trigger named samples (drums, breaks, one-shots)                      |
| `note("c e g")`                   | pitched notes; defaults to a synth unless `.sound()` given            |
| `n("0 2 4")`                      | sample variant index, **or** scale degree when paired with `.scale()` |
| `note("c e g").sound("sawtooth")` | play notes through a synth waveform                                   |

**Synth waveforms** (pass to `.sound()`): `sine`, `square`, `sawtooth`, `triangle`, plus
super-variants and `white`/`pink`/`brown` noise. FM synthesis: `.fm(idx)`, `.fmh(ratio)`,
`.fmattack/.fmdecay`. Additive: `.n()` with `.partials`, wavetables via sample names.

## Samples & banks

- This project preloads `github:tidalcycles/dirt-samples`. Common names: `bd sd hh oh cp
cr rim lt mt ht sn arpy bass breaks125 jazz east`.
- **`:n` picks a variant:** `sound("sd:0 sd:3 sd:5")`. Index wraps if out of range.
- **`.bank("RolandTR909")`** prefixes a kit so plain names resolve to that bank's samples.
- Load more: `samples("github:user/repo")` or a URL map in `initStrudel({ prebake })`.

## The effect catalog

### Filters

| Control                             | Aliases         | Effect                                                                      |
| ----------------------------------- | --------------- | --------------------------------------------------------------------------- |
| `.lpf(hz)`                          | `cutoff`, `ctf` | low-pass cutoff                                                             |
| `.hpf(hz)`                          | `hcutoff`       | high-pass cutoff                                                            |
| `.bpf(hz)`                          | `bandf`         | band-pass center                                                            |
| `.lpq(q)` / `.hpq` / `.bpq`         | `resonance`     | filter resonance/Q                                                          |
| `.lpenv(amt)` `.lpa/.lpd/.lps/.lpr` | —               | filter envelope amount + ADSR (also `hp*`, `bp*`)                           |
| `.vowel("a e i o u")`               | —               | formant filter — single letters only (`oo`/`aa` → `unknown vowel`, dropped) |

### Amplitude envelope (ADSR)

| Control                   | Effect                                       |
| ------------------------- | -------------------------------------------- |
| `.attack(s)` / `.att`     | fade-in time                                 |
| `.decay(s)` / `.dec`      | drop to sustain time                         |
| `.sustain(lvl)` / `.sus`  | held level 0..1                              |
| `.release(s)` / `.rel`    | fade-out after note ends                     |
| `.adsr("a:d:s:r")`        | all four at once                             |
| `.gain(x)`                | per-event volume (≈0..1.5)                   |
| `.velocity(x)`            | velocity scaling                             |
| `.legato(x)` / `.clip(x)` | scale event duration (note overlap/staccato) |

### Space — reverb & delay

| Control                  | Aliases  | Effect                                                        |
| ------------------------ | -------- | ------------------------------------------------------------- |
| `.room(x)`               | `reverb` | reverb send amount                                            |
| `.size(x)` / `.roomsize` | `sz`     | reverb size/tail                                              |
| `.roomlp` / `.roomdim`   | —        | reverb tone/damping                                           |
| `.delay(x)`              | —        | delay send amount                                             |
| `.delaytime(s)`          | `dt`     | delay time                                                    |
| `.delayfeedback(x)`      | `dfb`    | delay feedback (echo decay)                                   |
| `.orbit(n)`              | —        | route to a separate fx bus (isolate reverbs/delays per layer) |

### Color & motion

| Control                                        | Effect                                                   |
| ---------------------------------------------- | -------------------------------------------------------- |
| `.pan(0..1)` / `.panwidth`                     | stereo position                                          |
| `.speed(x)`                                    | playback rate (negative = reverse, also pitches samples) |
| `.coarse(n)`                                   | sample-rate reduction (bitcrush-ish, downsampling)       |
| `.crush(bits)`                                 | bit-crush                                                |
| `.shape(x)` / `.distort(x)`                    | waveshaping distortion / drive                           |
| `.phaser(rate)` `.phaserdepth` `.phasercenter` | phaser sweep                                             |
| `.vibrato(rate)` / `.vib`, `.vibmod`           | pitch vibrato                                            |
| `.tremolo` / `.tremolorate`, `.tremolodepth`   | amplitude tremolo                                        |
| `.leslie(x)` `.lrate` `.lsize`                 | rotary speaker                                           |
| `.djf(x)`                                      | DJ-style combined low/high pass (0=lp, 1=hp)             |

## Chaining order

Order generally doesn't change routing (controls accumulate into one event), but read it
top-to-bottom as "what is this sound": **source → pitch/structure → tone(filter/env) →
space(room/delay) → level(gain)**.

```js
note("c2 eb2 g2 bb1")
  .sound("sawtooth") // source
  .lpf(700)
  .lpq(8) // tone
  .decay(0.15)
  .sustain(0) // pluck envelope
  .room(0.3)
  .delay(0.25) // space
  .gain(0.9); // level
```

## Sound-design recipes

```js
// acid bass
note("c2 [eb2 g2] f2 [ab2 bb1]")
  .sound("sawtooth")
  .lpf(sine.range(300, 1200).slow(4))
  .lpq(10)
  .decay(0.15)
  .sustain(0);

// lush pad
note("<c4,eb4,g4 f4,ab4,c5>")
  .sound("sawtooth")
  .attack(0.5)
  .release(1)
  .lpf(1500)
  .room(0.6)
  .gain(0.5);

// crunchy break
sound("breaks165").chop(8).speed("<1 1.5 .5>").coarse(4).shape(0.3);
```
