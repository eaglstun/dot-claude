---
semantic_id: "TlmJLJ6xTtrtkPn2jO0KgzQ9p0jGQAAB"
related_ids:
  - "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
  - "-njdZsc1wbC30Lm-nDEhaHEwt9zikAAO"
---
# Open weights

**Open weights** means the company that trained a model published the actual trained
[[parameters]] - the billions of numbers that _are_ the model - so you can download the file and
run it on your own hardware instead of renting the model through someone else's API. Qwen, Llama,
Mistral, DeepSeek, and Gemma are open-weight; GPT-4 and Claude are not.

It is a narrower thing than "open source," and the difference matters. Open source, in the
traditional sense, means you get everything you'd need to rebuild the thing yourself: for a model
that would be the training data, the training code, and the recipe. Open _weights_ usually means
you get only the finished numbers - the cake, not the ingredient list or the instructions. You can
eat it, slice it, even re-frost it with a [[lora]] fine-tune, but you can't rebake it from scratch,
and you often can't see what went into it. Many "open" models also ship with a license that
restricts commercial use or bans certain applications, which is a further step away from what open
source classically meant.

What you _can_ do with open weights is most of what people actually want: run the model offline
with no API bill and no data leaving your machine, inspect and measure its behavior directly,
shrink it with [[quantization]] into a [[gguf]] file that fits on a laptop, fine-tune it into a
narrower or weirder version of itself, and keep running it unchanged for as long as you like - no
vendor can deprecate a model you already have on disk. That last point is the quiet one: an
open-weight model is the only kind nobody can take away from you.

**See also:** [[parameters]]: the trained numbers that get published; [[qwen]]: a prominent
open-weight family; [[gguf]]: the format open weights usually get packaged into for local use;
[[lora]]: how you cheaply customize an open-weight model; [[mixture-of-experts]]: an architecture
common in the largest open-weight releases.
