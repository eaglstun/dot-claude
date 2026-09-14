# Pattern functions

The transform vocabulary you chain onto patterns. All are methods after `initStrudel()`
(also importable as standalone functions). Grouped by the job they do. Most take either a
plain value or a mini-notation string, so e.g. `.fast(2)` and `.fast("<1 2>")` both work.

## Time & speed

| Fn                              | Does                                                                  |
| ------------------------------- | --------------------------------------------------------------------- |
| `.fast(n)` / `.slow(n)`         | compress / stretch into the cycle (`.fast(2)` = twice as quick)       |
| `.hurry(n)`                     | like `.fast` but also pitches samples up (changes `speed`)            |
| `.rev()`                        | reverse the cycle                                                     |
| `.iter(n)`                      | each cycle, rotate the sequence start by 1/n                          |
| `.iterBack(n)`                  | `iter` the other direction                                            |
| `.palindrome()`                 | alternate forward / reversed each cycle                               |
| `.early(t)` / `.late(t)`        | nudge events earlier / later (in cycles)                              |
| `.swingBy(amt,n)` / `.swing(n)` | add swing to every nth subdivision                                    |
| `.ply(n)`                       | repeat each event n times in place (`"bd sd".ply(2)` = `bd bd sd sd`) |
| `.segment(n)`                   | sample a continuous pattern into n discrete events/cycle              |
| `.range(lo,hi)`                 | scale a 0..1 signal into `lo..hi` (use with `sine`, `saw`, etc.)      |

## Structure & rhythm

| Fn                                   | Does                                                       |
| ------------------------------------ | ---------------------------------------------------------- |
| `.euclid(k,n)` / `.euclidRot(k,n,r)` | apply Euclidean rhythm to a pattern                        |
| `.euclidLegato(k,n)`                 | euclid where hits sustain to the next hit                  |
| `.struct("x ~ x x")`                 | impose a boolean rhythm onto a value pattern               |
| `.mask("1 0 1 1")`                   | keep events only where the mask is truthy                  |
| `.chop(n)`                           | slice each sample into n pieces played in order (granular) |
| `.striate(n)`                        | like chop but interleaves slices across events             |
| `.slice(n, "0 2 1 3")`               | cut sample into n parts, play named indices                |
| `.splice(n, …)`                      | `slice` that time-stretches each part to fit               |
| `.chunk(n, fn)`                      | apply `fn` to a different 1/n chunk each cycle             |
| `.run(n)`                            | generate `0 1 2 … n-1` as a pattern                        |

## Randomness & variation

| Fn                                                         | Does                                                       |
| ---------------------------------------------------------- | ---------------------------------------------------------- |
| `.degradeBy(p)` / `.degrade()`                             | randomly drop events with probability p (default .5)       |
| `.undegradeBy(p)`                                          | the complementary drops (pairs with `degradeBy` for fills) |
| `.sometimesBy(p, fn)`                                      | apply `fn` to events with probability p                    |
| `.sometimes/.often/.rarely/.almostAlways/.almostNever(fn)` | preset probabilities                                       |
| `.someCyclesBy(p, fn)`                                     | apply `fn` to whole cycles with probability p              |
| `rand`, `rand2`, `perlin`                                  | continuous signals 0..1 (use with `.range`, `.segment`)    |
| `irand(n)`                                                 | random integers 0..n-1                                     |
| `.choose(...)` / `chooseCycles(...)`                       | pick randomly per event / per cycle                        |
| `.shuffle(n)` / `.scramble(n)`                             | reorder n slices (shuffle = no repeats, scramble = with)   |

## Layering, stereo & echo

| Fn                                    | Does                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------ |
| `stack(a, b, …)`                      | play patterns simultaneously (also `,` in mini-notation)                 |
| `.superimpose(fn)`                    | layer a transformed copy over the original                               |
| `.off(t, fn)`                         | layer a copy shifted by `t` cycles and transformed (delay/echo feel)     |
| `.jux(fn)`                            | original in left channel, `fn(original)` in right (classic: `.jux(rev)`) |
| `.juxBy(amt, fn)`                     | `jux` with adjustable stereo width                                       |
| `.echo(n, t, fb)` / `.stut(n, fb, t)` | n echoes spaced by `t`, each `fb` quieter                                |
| `.add(n)` / `.sub(n)`                 | offset note/number values (transpose by adding)                          |

## Conditionals & sequencing over time

| Fn                                                   | Does                                                      |
| ---------------------------------------------------- | --------------------------------------------------------- |
| `.every(n, fn)`                                      | apply `fn` every nth cycle                                |
| `.everyBy(n, p, fn)` / `.firstOf` / `.lastOf(n, fn)` | variants of `every`                                       |
| `.when(boolPat, fn)`                                 | apply `fn` when the boolean pattern is true               |
| `.chunk(n, fn)`                                      | (see structure) walk `fn` across chunks over n cycles     |
| `cat(a,b,…)` / `slowcat`                             | one pattern per cycle, in sequence                        |
| `fastcat(a,b,…)` / `seq`                             | squeeze all into one cycle (same as space-separated)      |
| `arrange([n, pat], …)`                               | play `pat` for n cycles, then the next — song arrangement |
| `.ribbon(start, len)`                                | loop a `len`-cycle window starting at cycle `start`       |

## Pitch & harmony

| Fn                                       | Does                                                           |
| ---------------------------------------- | -------------------------------------------------------------- |
| `.scale("C:minor")`                      | map `n()` degrees onto a scale (`n("0 2 4").scale("C:major")`) |
| `.transpose(n)` / `.add(note("…"))`      | shift pitch by semitones / intervals                           |
| `.voicing()` / `.chord("Cm7").voicing()` | turn chord symbols into voiced notes                           |
| `note("c@maj e@min")`, `.rootNotes(oct)` | chord + root helpers                                           |

## Quick patterns

```js
// build then vary
sound("bd*4, hh*8")
  .sometimesBy(0.3, (x) => x.speed(2))
  .every(4, rev);

// euclid groove with stereo motion
sound("hh(7,16)").jux(rev).pan(sine.range(0, 1).slow(4));

// melodic line from scale degrees
n("0 2 4 6 4 2").scale("<C:minor D:dorian>").sound("piano").slow(2);

// granular texture
sound("breaks165")
  .chop(16)
  .rev()
  .sometimesBy(0.2, (x) => x.speed(-1));
```
