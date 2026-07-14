---
topic_id: "v2:JHBC"
topic_path: "ai-concepts"
semantic_id: "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
related_ids:
  - "S05HSldIThUYdhlyoOTexxM8Q7ymUAAJ"
  - "TQDbGF_lWQUd5pFwK02S1X9ww_5EUAAE"
---
# GAN

**GAN** (Generative Adversarial Network) is a type of generative [[machine-learning]] model,
introduced by Ian Goodfellow and colleagues in 2014, built from two neural networks set
against each other. The **generator** starts from a random vector in [[latent-space]] and
tries to produce realistic fakes (say, images). The **discriminator** is shown a mix of real
and fake samples and tries to tell them apart. They train as rivals (the generator keeps
getting better at fooling the discriminator while the discriminator keeps getting better at
catching it) until, ideally, the fakes are indistinguishable from the real thing. GANs drove
an era of photorealistic face generation (StyleGAN) and image-to-image translation, but
they're notoriously finicky to train (a common failure is _mode collapse_, where the
generator churns out the same few outputs). For general image generation they've largely been
overtaken by diffusion models, though they still shine where fast, one-shot sampling matters.

**See also:** [[latent-space]]: the generator's input lives here.
