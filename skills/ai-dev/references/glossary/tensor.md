---
topic_id: "v2:JNOB"
topic_path: "ai-concepts/mathematical-basics"
semantic_id: "Zik2asZFTCSP7_neJMQO9XFwuz7ikAAN"
related_ids:
  - "enk0fq4US4C077zyvNeCdXFQmRzqkAAP"
  - "8mv24oylSCKM6_tWENoPFJ0BuhrnwAAC"
---
# Tensor

**Tensor** is the basic data structure of modern [[machine-learning]]: a grid of numbers with
any number of dimensions. It generalizes the familiar cases (a single number is a 0-D tensor,
a list of numbers is 1-D, a table (matrix) is 2-D) to as many dimensions as you need; a batch
of color images, for instance, is a 4-D tensor of shape `[batch, height, width, channels]`.

Every input, weight, and intermediate value in a neural network is a tensor, and training is
basically a long chain of tensor operations (matrix multiplies, additions, and simple
nonlinear steps). Frameworks like PyTorch, TensorFlow, JAX, and [[mlx]] are built around
tensors and run those operations on accelerators (GPUs/TPUs), hardware whose whole job is
doing this kind of math massively in parallel.

Two properties matter most day to day: _shape_
(the size along each dimension, the usual source of bugs) and _dtype_ (how precisely each
number is stored, e.g. fp32/fp16/bf16, trading accuracy for speed and memory). One note: the
ML "tensor" is really just a multidimensional array, and is looser than the stricter
math/physics meaning of the word.
