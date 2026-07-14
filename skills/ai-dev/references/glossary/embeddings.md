---
topic_id: "v2:JFGN"
topic_path: "ai-concepts/vector-representation"
semantic_id: "Yg0fKTZS7rmLH2wGBDQc7iyaiz7tEAAA"
related_ids:
  - "ABvHYhhCoiOTO20ntGAN7D4er1n_cAAB"
  - "5ChOalbUZ70LDhhbwJAM_l8yYb7kAAAJ"
---
# Embeddings

**Embeddings** are a way of turning things (words, sentences, images, products, users) into
lists of numbers (vectors) arranged so that _distance and direction carry meaning_. The older
approach was to give each word an arbitrary ID, or a giant list that's all zeros except a
single 1 (a "one-hot" vector), which tells you nothing about how words relate.

An embedding
instead maps each word to a few hundred or few thousand real numbers (e.g. 768
[[dimensions]]) where related items land near each other. They come out of training a model
and reading off one of its internal layers; the resulting vectors live in a [[latent-space]],
which is what makes the famous "king − man + woman ≈ queen" arithmetic work.

In practice
embeddings power semantic search, recommendations, clustering, and **RAG**
(retrieval-augmented generation: looking up relevant text to feed a model): you turn a query
into a vector and find the closest stored vectors. Those vectors are just [[tensor]]s, and at
scale they're kept in a **vector database** built for fast nearest-neighbor lookup.

**See also:** [[latent-space]], the space embeddings live in; [[dimensions]], what their
length is measured in; [[tensor]], what an embedding actually is.
