---
semantic_id: "n84tpCbFQoiKfj1RmIrexXHHrhfAsAAK"
related_ids:
  - "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
  - "bOwNXd7GZoiJPszwEdrFxXALfQbOQAAC"
---
# Checkpoint

A **checkpoint** is a saved snapshot of a model's [[parameters]] at one moment during
training, written to disk so the run can be resumed, compared against other moments, or
rolled back. Training is a long downhill walk (see [[gradient-descent]]); a checkpoint is a
photograph of exactly where the weights were standing at step N.

A full checkpoint holds more than the weights. It also carries the optimizer state, the
running momentum and per-parameter statistics the training algorithm has built up, because
without those you can _run_ the model but you cannot cleanly _continue_ the run: restart
from weights alone and the optimizer has to rebuild its momentum from a standing start.
Weights-only files are still called checkpoints, and are what you want for inference or
publishing, just not for resuming.

Frequency is a storage tradeoff. Each checkpoint is a complete copy of the model, so a
common pattern is to save every N steps, keep only the most recent few, and separately keep
whichever one scored best. With [[lora]] the arithmetic changes completely: the checkpoint
is the adapter alone, megabytes instead of gigabytes, which is why adapter training can
afford to keep every step it ever took.

"Best" is usually scored by [[val-loss]], and this is the part worth knowing: the
lowest-validation-loss checkpoint is not automatically the model you want. Loss measures one
narrow thing, how surprised the model is by held-out text. A run can reach its best number
at a step where the behavior you were actually training is not there yet, or has already
been trained past. Checkpoints are the only way to see this at all, because probing several
from the same run turns "did this work" into a sequence you can watch a behavior arrive in,
or fail to.

The word does double duty. Outside of training, "checkpoint" is also the generic term for a
distributed file of trained weights, `.ckpt` and `.safetensors` files and the like, which is
the sense meant when an image or language model is described as having several checkpoints
available to download (see [[gguf]] for the local-inference packaging of the same idea).

**See also:** [[parameters]]: a checkpoint is a copy of exactly these, which is why the file
is the size of the model; [[val-loss]]: the usual score for picking the "best" checkpoint,
and the reason picking by it alone can mislead; [[lora]]: adapter checkpoints are tiny, so
you can keep all of them; [[gradient-descent]]: the walk a checkpoint is a snapshot of;
[[gguf]]: what a published checkpoint often gets packaged as for local use.
