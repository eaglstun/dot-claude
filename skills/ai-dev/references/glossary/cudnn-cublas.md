---
topic_id: "v2:KHIF"
topic_path: "cuda-gpu/gpu-libraries"
semantic_id: "-nhW1t8U_Zkt9M6eGjST57VRuZBj0AAM"
related_ids:
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
  - "5mvyFquWmY6l0ca6mjPDa_X1m7350AAK"
---
# cuDNN / cuBLAS

**cuBLAS** and **cuDNN** are NVIDIA's optimized math libraries that sit on top of [[cuda]] and
do the heavy lifting most ML frameworks depend on. **cuBLAS** is NVIDIA's GPU version of BLAS
(Basic Linear Algebra Subprograms), the matrix-multiply and vector routines that make up the
bulk of neural-network math. **cuDNN** (CUDA Deep Neural Network library) is a higher-level
toolkit tuned specifically for deep learning: convolutions, pooling, normalization, attention,
activation functions, and the like. Frameworks such as PyTorch and TensorFlow don't hand-write
GPU code for these. They call cuBLAS and cuDNN, which is a big reason NVIDIA hardware is so
fast and so entrenched. They're NVIDIA's counterpart to Apple's [[mps]] (and roughly what a
[[vulkan]] or [[metal]] backend has to rebuild to compete). Both are proprietary,
closed-source NVIDIA libraries, free to use, though cuDNN in particular needs a separate
download and registration from the base CUDA toolkit.

**See also:** [[cuda]]: the platform these libraries are built on; [[mps]]: Apple's
equivalent kernel library; [[tensor]]: the data structure their routines operate on.
