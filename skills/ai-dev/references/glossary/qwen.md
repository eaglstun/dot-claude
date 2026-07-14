---
topic_id: "v2:JKDC"
topic_path: "ai-concepts/architecture-types"
semantic_id: "TGvkGBO_HxdJfBFmE53XyTdEp2jkQAAI"
related_ids:
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
  - "IG2DMNG5pVX7shlyN68mrTVpZ3riUAAP"
---
# Qwen

**Qwen** is a family of open-weight large language models from Alibaba Cloud (the name is short
for Tongyi Qianwen, 通义千问). Like a [[gpt]], each Qwen model is a decoder-only [[transformer]]
trained to predict the next token. The part that matters in practice is the _open-weight_ part:
Alibaba publishes the actual trained [[parameters]], much of the family under the permissive
Apache 2.0 license, so anyone can download a Qwen model and run it on their own hardware instead
of renting it through someone else's API.

The family comes in generations (Qwen, Qwen1.5, Qwen2, Qwen2.5, Qwen3) and a wide spread of
sizes, from tiny half-billion-parameter models that fit on a phone up to very large
mixture-of-experts models in the hundreds of billions. There are specialized branches too:
**Qwen-Coder** for programming, **Qwen-VL** for images-plus-text, **Qwen-Audio** for sound, and
reasoning-focused variants. Because the weights are open and even the small sizes are genuinely
capable, Qwen has become one of the most common starting points for running models locally: it
ships in [[gguf]] form for llama.cpp and Ollama, and it's a frequent base for [[lora]] fine-tunes
that teach it a narrower job or a particular voice.

If [[gpt]] is the closed model you reach through an API, Qwen is the open one you can actually
hold: download it, inspect it, fine-tune it, run it offline. That difference is most of why it
turns up so often in local-inference and hobbyist projects, where the few flagship Qwen models
that stay API-only matter far less than the dozens you can just pull down and run.

**See also:** [[gpt]]: the other decoder-only LLM family, closed where Qwen is open;
[[transformer]]: the architecture both are built on; [[gguf]]: the file format that gets a Qwen
model running on your own machine; [[lora]]: the cheap way to fine-tune one for your own use.
