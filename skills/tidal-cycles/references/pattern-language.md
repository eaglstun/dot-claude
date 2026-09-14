# Pattern language and mini-notation

Sources: [Patterns](https://tidalcycles.org/docs/reference/patterns/), [Mini Notation](https://tidalcycles.org/docs/reference/mini_notation/), [Time](https://tidalcycles.org/docs/reference/time/), [Tutorial](https://tidalcycles.org/docs/getting-started/tutorial/)

## Mental model

Conceptually, `Pattern a` answers a time query with zero or more events carrying
values of type `a`. Transformations alter event timing, structure, or values without
requiring a fixed grid. `ControlPattern` is a pattern of parameter maps destined for
an output target, usually SuperDirt.

`d1 $ s "bd sd"` sends two sound events across one cycle. Adding more whitespace-
separated tokens fits them into the same cycle rather than lengthening it.

## Mini-notation

```text
~             rest
a b c         equal subdivisions of a cycle
[a b] c       fit a b into the first of two top-level steps
[a,b,c]       superimpose events
<a b c>       choose one item per cycle
a*3           speed/repeat a within its slot
a/3           slow a across three times its slot
a!3           replicate a as three equal sibling steps
a?            randomly degrade events
a(3,8)        Euclidean rhythm: 3 events over 8 steps
{a b, c d e}  polymeter; concurrent sequences with independent step counts
sound:2       select zero-based sample variant
```

`*` and `!` are not interchangeable: `"bd*3 sd"` fits three kicks into the
first half-cycle, while `"bd!3 sd"` creates four equal top-level steps.

Mini-notation values are overloaded. `s "bd"`, `n "0 2 4"`, `gain "0.5 1"`,
and `speed "1 -1"` parse the same rhythmic syntax into different value types.

## Combining patterns

```haskell
stack [s "bd*4", s "~ sd ~ sd"]
s "bd sd" # gain "0.8 1"
n "0 2 4" # s "superpiano"
```

- `stack` overlays whole patterns.
- `#`/`|>` combine control maps using the structure/alignment defined by those
  operators. Do not blindly replace one merge operator with another.
- `$` is Haskell's low-precedence application: `f $ g $ x` means `f (g x)`.
- `.` composes transformations: `every 4 (rev . fast 2)`.

## High-value transformations

- Time: `fast`, `slow`, `hurry`, `rev`, `rotL`, `rotR`, `within`, `zoom`.
- Conditional: `every`, `whenmod`, `sometimes`, `sometimesBy`.
- Layering: `stack`, `superimpose`, `off`, `jux`, `juxBy`, `echo`, `echoWith`.
- Structure: `struct`, `mask`, `euclid`, `iter`, `chop`, `striate`.
- Sequencing: `cat`, `slowcat`, `fastcat`, `timeCat`.

Patterns are polymorphic, so a numeric transform can itself be patterned:

```haskell
d1 $ fast "1 2 4 2" $ s "bd sd"
d2 $ every 4 rev $ n "0 2 [4 7] 5" # s "superpiano"
```

## Time pitfalls

- `rev` reverses each cycle independently. Use `outside` for a transform over a
  larger time window.
- `fast` changes event density but not sample playback pitch; `hurry` also changes
  the `speed` control.
- `off t f` keeps the original and overlays a delayed transformed copy.
- Prefer exact fractions such as `1/8` when alignment matters.

## Gotchas

- At top level, superposition needs brackets: `"[bd*3, hh*4]"`.
- `/` stretches time; `%` denotes a numeric ratio or polymetric subdivision.
- A compile error near `#` is often grouping or incompatible value types.
- Native Tidal treats note zero as `c5` in its MIDI mapping.

