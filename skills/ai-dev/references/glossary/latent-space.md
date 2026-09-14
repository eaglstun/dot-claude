---
topic_id: "v2:JNPO"
topic_path: "ai-concepts/mathematical-basics"
semantic_id: "5ChOalbUZ70LDhhbwJAM_l8yYb7kAAAJ"
related_ids:
  - "Yg0fKTZS7rmLH2wGBDQc7iyaiz7tEAAA"
  - "Zik2asZFTCSP7_neJMQO9XFwuz7ikAAN"
---
# Latent space

**Latent space** is the abstract, usually much smaller space in which a model holds the
compressed "essence" of its input. Rather than work with raw pixels or words, the model maps
each input to a point (a vector) in this space, where each axis captures some feature the
model _learned_ on its own rather than one a human labeled, hence _latent_, meaning hidden.
The useful part is that geometry turns into meaning: similar inputs land near each other, and
moving in a particular direction can correspond to a meaningful change (the classic
"king − man + woman ≈ queen" with word embeddings). Many kinds of models rely on it:
autoencoders, diffusion models, embedding models, and generative models (a [[gan]], say) work
by picking or nudging a point in latent space and then translating it back out into an image,
text, or audio.

**See also:** [[gan]]: generates data by mapping latent vectors to realistic outputs;
[[dimensions]]: the high-dimensional axes this space is measured in; [[embeddings]]: the
vectors that populate this space.
