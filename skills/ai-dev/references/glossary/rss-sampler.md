---
topic_id: "v2:JDPE"
topic_path: "ai-concepts/mixed"
semantic_id: "A7StbWApznlvLpyaOZrc1kK9ZjfWAAAN"
related_ids:
  - "AsAVL1BJztrjfJp9JZ65c2b5Jm9pMAAO"
  - "VqWBJfUu8muHyBteNFiyUtH8eufYAAAB"
---
# RSS sampler

An **RSS sampler** is a small monitor that wakes up on a timer, reads a process's **RSS**
(Resident Set Size, the slice of its memory actually resident in physical RAM, as opposed to
swapped out to disk or merely reserved on paper), and logs the number. String those readings
together and you get a memory _trajectory_: a curve of real footprint over time instead of a
single after-the-fact figure. "Self-monitoring" just means the process samples _itself_: it
spins up a little background thread that watches its own RSS while the real work runs, so you
don't need an external `top`/`ps` babysitter racing to catch the peak before it vanishes.

The reason you reach for one is the OOM cliff. A long job, say, chewing through a 730-second
audio file, can sail along for minutes and then get killed outright by the operating system
the instant its footprint crosses what the machine physically has. A lone "peak memory" number
tells you _that_ it died, not _when_ or _how fast it was climbing_. The trajectory tells you
the shape: flat and safe, a slow creep with room to spare, or a leak that ramps until it walks
off the edge. That's the difference between "fp16 halves the footprint, so the small model
should survive the file that killed the fp32 run" being a hope and being a measurement.

It pairs naturally with the memory levers on the model side. The footprint RSS measures is
driven mostly by a model's [[parameters]] and the numeric precision they're stored at, which
is exactly what quantized formats like [[gguf]] and the engines that load them ([[ggml]]) exist
to shrink. An RSS sampler is how you check whether that shrink actually bought enough headroom
on _this_ machine, for _this_ workload, instead of trusting the arithmetic and finding out at
second 730.

**See also:** [[parameters]]: the count that drives the footprint; [[gguf]]: quantization,
the main lever for shrinking it; [[ggml]]: the engine that loads those weights into the RAM
you're watching.
