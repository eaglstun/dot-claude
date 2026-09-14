---
topic_id: "v2:DJDK"
topic_path: "model-runners"
semantic_id: "6GoCS57xrcsNNN0bF6OKD5Ay_9BiwAAF"
related_ids:
  - "6OACWp0ZydlBueUbX7fPjxYyb0NCwAAI"
  - "-nhW1t8U_Zkt9M6eGjST57VRuZBj0AAM"
---
# llama.cpp vs Ollama

First, the naming: "llama" here means **llama.cpp** (the software that runs models), not Meta's
**Llama** model family. Ollama's name is a play on it, which is fitting because **Ollama is
built on top of llama.cpp**, they're not really competitors so much as different layers of the
same stack.

**llama.cpp** is the low-level C/C++ engine (powered by [[ggml]]) that actually runs [[gguf]]
models. It's a library plus command-line tools (`llama-cli`, `llama-server`) and ships the GPU
backends: [[cuda]], [[metal]], [[vulkan]], for handing work to the GPU. It's maximally
flexible and fast, but you manage everything yourself: find the right `.gguf`, pick the
quantization (how much the model is shrunk), set the context length and GPU flags, wire up the
chat template.

**Ollama** wraps that engine to make it easy to use. It adds a model catalog
(`ollama pull llama3`), automatic download and caching, sensible defaults baked into a
`Modelfile`, and a background server that other apps can talk to over a simple web API
(including an OpenAI-compatible one). You give up some fine control in exchange for not having
to think about any of the plumbing.

Rule of thumb: reach for **Ollama** when you want a model running in one command with a clean
local API; drop down to **llama.cpp** when you need the newest features, custom build options,
or to squeeze out maximum performance. (LM Studio is a third option, a point-and-click app
over the same llama.cpp core.)

**See also:** [[gguf]], the model format both run; [[ggml]], the library underneath
llama.cpp; [[metal]], [[cuda]], [[vulkan]], the GPU backends llama.cpp offloads to.
