---
topic_id: "v2:JDEI"
topic_path: "ai-concepts/mixed"
semantic_id: "DT66WEb8QXjJDj9MOEwG0nXaY97tUAAB"
related_ids:
  - "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
  - "SQaeEHTSr7wrDhxgJOpVw3PII9zoUAAF"
---
# Temperature

**Temperature** is the single knob that decides how adventurous a language model is allowed to
be when it picks each next word. Before a model like a [[gpt]] commits to a token, it doesn't
have one answer in hand, it has a whole spread of candidates with odds attached: maybe 60% "the",
20% "a", 5% "an", and a long tail of unlikely stragglers. Temperature reshapes that spread right
before the dice are thrown. Turn it down and the odds get sharper, the favorite gets even more
favored, and the model plays it safe. Turn it up and the odds flatten out, the longshots get a
real seat at the table, and the model gets loose, surprising, eventually unhinged.

Mechanically it's one division. The model's raw scores (the "logits") get divided by the
temperature value before they're turned into probabilities. Divide by a small number and you
exaggerate the gaps between candidates; divide by a big one and you squash them toward equal.
The usual dial runs from 0 to about 2. At **temperature 0** there's no gamble left at all: the
model takes the single most likely token every time, which makes it deterministic and repeatable
(same prompt in, same answer out). Around **0.7 to 1.0** is the everyday range, enough spice to
sound human without falling apart. Push past **1.5** and coherence starts to dissolve into word
salad.

One thing temperature is _not_: it's not the random seed. The seed fixes _which_ roll of the dice
you get; temperature decides how loaded the dice are in the first place. You can hold one steady
and move the other. A clean example lives in the deep-dive [On the Machine We Switched
Off](/deep-dives/1930-on-the-machine-we-switched-off/), where a 1930-trained model is interviewed
twice with the temperature pinned at 0.8 and the seed pinned at 1930, so the _only_ thing changing
between runs is the language of the questions. Freezing temperature is what makes that an
experiment instead of an anecdote: it takes randomness off the table as a suspect.

**See also:** [[gpt]]: the next-token predictor whose probability spread temperature reshapes;
[[transformer]]: the architecture producing those scores in the first place; [[gguf]]: when you
run a model locally, temperature is one of the sampling flags you set yourself; [[llamacpp-vs-ollama]]:
the local engines where you actually turn this dial at the command line.
