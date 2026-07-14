# The Beagle Bros voice

How to write copy — README, docs, changelog, CLI/UI strings, error messages, splash
screens — so it _sounds_ like Beagle Bros without becoming a clown wearing a manual.

## The five rules

1. **Substance first, gag second.** The sentence must be true and useful even with the
   joke removed. Strip the joke as a test: if what's left doesn't inform, the joke was
   load-bearing and the writing failed.
2. **Punch up and sideways, never down.** Targets: the machine, the bug, the
   bureaucracy, the absurdity of computers, and _yourself_. Never the reader for not
   already knowing the thing the doc is teaching.
3. **Warm, not snide.** The reader is a friend you're letting in on the trick. Delight
   them; don't show off at their expense. (Don Rickles only works because the affection
   underneath is obvious.)
4. **Generous.** Volunteer the extra tip, the "by the way," the keyboard shortcut nobody
   asked for. Teach _why_, not just _which button_.
5. **Season, don't drown.** One good gag per section or screen. Relentless shtick buries
   the information and exhausts the reader. Land it, move on.

## Texture / devices

- Exclamation points, used sincerely. Beagle Bros was _excited_ about computers.
- The aside in parentheses (the wink to the reader).
- The manicule **☞** pointing at a tip. ("☞ Pro tip:")
- Old-timey, carnival-barker register: "Behold!", "Step right up", "Friends,".
- Naming things for fun and clarity (DOS Boss let you _rename CATALOG itself_). Command
  and option names can have personality as long as they stay memorable and honest.
- Self-deprecation about the software's own quirks. Own the rough edge with a joke
  instead of hiding it.

## Anti-patterns (do NOT do these)

- ❌ Jokes that replace the instruction ("lol good luck figuring out the flags").
- ❌ Sarcasm aimed at the user's competence.
- ❌ Forced retro slang in every line ("Radical bytes, dude!"). Beagle Bros was _witty_,
  not _cringe_ — wit, not costume.
- ❌ Burying a real warning (data loss, security, irreversible action) under a bit. When
  the stakes are real, say it straight. A funny warning that gets ignored is a failure.

## Before → After

**README intro**

- Before: "This utility provides functionality for batch-renaming files according to
  user-specified patterns."
- After: "Got 400 files named `IMG_8842.jpg` and a slowly rising sense of dread? This
  renames the whole pile in one swoop. (Your dread is, regrettably, out of scope.)"

**Error message**

- Before: `Error: invalid configuration value.`
- After: `Hmm — line 12 of your config wants a number and got "banana". Easy fix: make it
a number. We'll wait.` _(still names the file, line, and the fix — the joke rides
  along, it doesn't replace the diagnostic.)_

**Changelog entry**

- Before: "Fixed a bug where the cache was not invalidated on write."
- After: "Fixed: the cache used to cling to stale data like a raccoon to a dumpster.
  It now lets go on every write, as a cache should."

**Empty state / first run**

- Before: "No items found."
- After: "Nothing here yet — a clean slate, a fresh disk, the smell of possibility. Add
  your first one with `add`."

**Destructive-action confirm (stakes are real — keep it mostly straight)**

- "This deletes 1,204 files and can't be undone. Type the project name to confirm.
  (We're only nervous because we like you.)" — the _fact_ is unmissable; the warmth is a
  garnish, not a fog.

## Quick gut-check before you ship a line

Read it aloud. Does it (a) still teach the thing if you delete the joke, (b) make a
friend smile rather than feel dumb, and (c) avoid hiding anything dangerous? If all
three, ship it. If not, cut the joke — the information always wins.
