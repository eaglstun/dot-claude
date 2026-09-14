---
topic_id: "v2:JDDK"
topic_path: "ai-concepts/mixed"
semantic_id: "SQaeEHTSr7wrDhxgJOpVw3PII9zoUAAF"
related_ids:
  - "DT66WEb8QXjJDj9MOEwG0nXaY97tUAAB"
  - "ZRKel9DjpyEVT01DpeNVnJ-HKfjpUAAK"
---
# Token

**Tokens** are the pieces a language model actually reads and writes. The model never sees
letters or whole words the way you do; before any text reaches it, a **tokenizer** chops that
text into chunks drawn from a fixed vocabulary (each chunk is a token) and hands the model the
ID number of each one. Every input and every output happens in this unit.

The chunks are usually _subwords_, not words. A common word like "cat" is a single token; a
rarer one like "unbelievable" might split into three ("un", "believ", "able"); a typo, an
emoji, or a snippet of code breaks into whatever fragments the vocabulary already has. This is
a deliberate compromise: keep the vocabulary small enough to be workable (typically 30k-200k
tokens) while still being able to spell out any word, name, or garbage string by combining
pieces. A rough rule of thumb for English is that one token runs about four characters, or
roughly three-quarters of a word.

<figure class="tok-demo">
<p class="tok-demo-sentence">Tokenizers read postpostmodern as pieces, not one word.</p>
<div class="tok-demo-row" role="img" aria-label="The sentence split into thirteen tokens, each with its numeric ID: Token 3323, izers 12230, read 1349, post 1736, post 2203, modern 49789, as 438, pieces 9666, comma 11, not 537, one 825, word 3409, period 13.">
<span class="tok"><span class="tok-t">Token</span><span class="tok-id">3323</span></span><span class="tok"><span class="tok-t">izers</span><span class="tok-id">12230</span></span><span class="tok"><span class="tok-t"><span class="tok-sp">·</span>read</span><span class="tok-id">1349</span></span><span class="tok"><span class="tok-t"><span class="tok-sp">·</span>post</span><span class="tok-id">1736</span></span><span class="tok"><span class="tok-t">post</span><span class="tok-id">2203</span></span><span class="tok"><span class="tok-t">modern</span><span class="tok-id">49789</span></span><span class="tok"><span class="tok-t"><span class="tok-sp">·</span>as</span><span class="tok-id">438</span></span><span class="tok"><span class="tok-t"><span class="tok-sp">·</span>pieces</span><span class="tok-id">9666</span></span><span class="tok"><span class="tok-t">,</span><span class="tok-id">11</span></span><span class="tok"><span class="tok-t"><span class="tok-sp">·</span>not</span><span class="tok-id">537</span></span><span class="tok"><span class="tok-t"><span class="tok-sp">·</span>one</span><span class="tok-id">825</span></span><span class="tok"><span class="tok-t"><span class="tok-sp">·</span>word</span><span class="tok-id">3409</span></span><span class="tok"><span class="tok-t">.</span><span class="tok-id">13</span></span>
</div>
<figcaption>Thirteen tokens, split by a local <a href="/glossary/qwen/">Qwen</a> tokenizer. The word <em>Tokenizers</em> alone breaks in two and <em>postpostmodern</em> into three; the comma and period are tokens of their own; and the faint dot marks the leading space that rides along inside a token. The number under each piece is the ID the model actually receives: to it, this sentence is the list <em>[3323, 12230, 1349, ...]</em>, and the words are only here for us.</figcaption>
</figure>

Tokens are the through-line of the whole pipeline. Each token is mapped to an [[embeddings]]
vector on the way in; [[attention]] is the mechanism by which tokens weigh each other; the
[[transformer]] chews on the whole sequence of them at once; and generation is just predicting
the next token over and over, with [[temperature]] deciding how boldly the model gambles among
the likely candidates. It is also why the practical limits you hear quoted are counted in
tokens rather than words: a model's **context window** (how much it can hold in view at once)
and, for hosted models, the bill are both measured per token.

**See also:** [[embeddings]]: what each token becomes once it is inside the model;
[[attention]]: how tokens weigh each other; [[transformer]]: the architecture that processes a
whole sequence of tokens at once; [[temperature]]: the knob that picks among candidate next
tokens; [[gpt]]: the next-token predictor built entirely around this unit.
