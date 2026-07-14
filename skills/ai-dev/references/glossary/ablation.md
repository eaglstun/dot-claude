---
topic_id: "v2:JPNM"
topic_path: "ai-concepts/experimental-methods"
semantic_id: "5-oGLN6CYtUJFB1shCYUwW6Ndr1UEAAI"
related_ids:
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
  - "718sDU7GXzjMVg1OzHwc5eWBpT7mIAAG"
---
# Ablation

**Ablation** is the practice of removing a piece of a model or its training setup on purpose,
just to see how much that piece mattered. The word is borrowed from surgery, where it means
cutting away tissue, and the method is about that clinical: if you suspect some component is
doing real work, take it out, run the model again, and measure how much worse it gets. That
drop (or the lack of one) is your answer. A big drop means the part was load-bearing; no
change means it was decoration.

The standard form is the **ablation study**, the table near the
end of nearly every [[machine-learning]] paper where the authors knock out one ingredient at a
time: an attention head, a layer, a loss term, a slice of training data, a preprocessing step,
and report what the score did. It's how a field that can't fully open the black box still
reasons about cause: not by explaining _why_ a part helps, but by proving _that_ it does, one
amputation at a time.

The thing you measure after each cut is usually a held-out metric like
[[val-loss]], and the component you're pulling is often a bundle of [[parameters]] you're
betting the model can live without. Done well, it separates the parts that earn their keep from
the ones that just came along for the ride. Done lazily (yanking several things at once), it
tells you nothing, because you can't say which cut caused the bleeding.

**See also:** [[machine-learning]]: the field where the ablation study is the standard proof
that a component matters; [[val-loss]]: the held-out score you watch rise or hold steady after
each cut; [[parameters]]: the weights an ablation removes to test whether they were pulling
their weight.
