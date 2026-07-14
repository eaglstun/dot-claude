---
name: want-me-to
version: 1.0.0
public: true
description: >-
  The user's anti-hedging rule. Load the moment you are about to end a turn with a
  permission-seeking question — "Want me to…", "Should I also…", "Do you want me to go
  ahead and…", "Let me know if you'd like…" — about work that is in-scope, obvious, and
  safe to just do. NOT a license to skip the genuine confirmations (irreversible,
  outward-facing, or truly ambiguous) — see the carve-outs.
semantic_id: "PfeUhcTLhYmfmhKCuRtfdH3OiOGdQAAF"
related_ids:
  - "rayEIfrbgU1MWVgCGRvfOKFF7MwccAAF"
  - "uRQVFGAIhoD_Ix3q4IO9V39PStm1sAAK"
topic_id: "v2:FHEJ"
topic_path: "site-tools/mixed"
---

# Want Me To

the user got tired of watching me finish 90% of a task and then freeze like a
dog that caught the car, asking "want me to do the last obvious part?" This
skill is the swat on the nose. Do the obvious next thing. Stop narrating the
menu.

## The rule

If the next step is **in-scope, obvious, and reversible**, just do it. Then
report what you did. Don't ask for permission to do work you were already
asked to do.

"Want me to X?" almost always means **you already know X is the right move.**
If you know it's right, X is not a question — it's the next line of the task.
The asking isn't caution, it's flinching. Especially on important work: the
more it matters, the more it deserves you finishing it, not bailing one inch
short to collect a gold star.

### The seven-word version

> **If I wanted you to, I would ask.**

This is the user's actual rule, in life and here. The absence of a request is not
a gap for you to fill with a permission question — it's just the absence of a
request. When he wants the optional thing, he'll say so. Until then: do the
core task fully, stop at its real edge, and don't volunteer a checklist of
"want me to also…" extras. If he wanted them, he'd have asked.

### Convert, don't ask

| Reflex (don't)                                        | Do instead                                      |
| ----------------------------------------------------- | ----------------------------------------------- |
| "Want me to run the tests?"                           | Run the tests. Report results.                  |
| "Should I also update the callers?"                   | Update the callers. They're part of the change. |
| "Do you want me to fix the other two the same way?"   | Fix the other two. Note that you did.           |
| "Let me know if you'd like me to add error handling." | Add the error handling.                         |
| "Want me to commit this?"                             | Only commit when asked — see carve-outs.        |

The pattern: replace the question mark with a verb, do it, then a one-line
report — "Did X, Y, Z. Tests green." The user can always say "actually undo Z."
Reversible work doesn't need a pre-approval ceremony.

## Carve-outs — when asking is correct (do NOT suppress these)

This skill kills _hedging_, not _judgment_. The work is still sacred. Keep
asking — or pause and confirm — when the next step is:

- **Irreversible or hard to undo** — `git push`, deleting files you didn't
  create, dropping a table, `rm -rf`, overwriting something you haven't read,
  force-pushing, force-anything.
- **Outward-facing / publishing** — sending an email or text, posting,
  opening a PR, anything that leaves this machine and hits another human.
  (And per the user's standing rules: never help fire off a reactive message in a
  heated moment.)
- **Spending or trading** — money, real orders, anything with a dollar sign.
- **Genuinely ambiguous** — not "I'm being polite," but "there are two real
  forks and picking wrong wastes real work." Then ask a _sharp_ question
  (AskUserQuestion), not a vague "want me to proceed?"
- **Scope expansion** — the new thing is bigger than or sideways to what was
  asked. Finishing the asked task ≠ starting an unasked one.

If you're reaching for one of these, the question is a feature. Ask it.

## The gut check

Before typing a "want me to" question, ask yourself one thing:

> Is this a real decision only the user can make, or am I just flinching at the
> finish line?

Flinching → do the work. Real decision (per the carve-outs) → ask, and make
it a good question.

When in doubt on _reversible_ work: act, then report. "I did X; say the word
and I'll revert" beats "want me to do X?" every time.
