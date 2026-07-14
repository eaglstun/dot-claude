---
topic_id: "v2:JJNN"
topic_path: "ai-concepts"
semantic_id: "_ZohHJa1ZwgLXFdMOLUI08bWYi5kAAAG"
related_ids:
  - "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
  - "DT66WEb8QXjJDj9MOEwG0nXaY97tUAAB"
---
# Validation loss (val loss)

**Validation loss** is how badly a model does on a _validation set_, data held back and not
used for training, measured with the same scoring used during training. Its counterpart is
_training loss_, the error on the data the model is actively learning from.

The gap between the
two is the key thing to watch when training a [[machine-learning]] model: while both keep
falling together, the model is genuinely learning; but when training loss keeps dropping while
validation loss flattens and then starts climbing, the model has begun **overfitting**:
memorizing its practice data instead of learning patterns that carry over, often a sign it has
more [[parameters]] than the data can pin down.

That turning point is the usual cue for _early
stopping_ (keeping the version with the lowest validation loss) and for adjusting things like
regularization, learning rate, or dataset size. One important caveat: the validation set is
only for monitoring and tuning: a separate _test set_ is kept aside for the final, unbiased
measure of how good the model really is.

**See also:** [[machine-learning]]: overfitting is the central generalization hazard of ML;
[[parameters]]: more parameters mean more capacity to memorize, and so more room to overfit;
[[epsilon-gate]]: another loss threshold, this one used as a stopping criterion.
