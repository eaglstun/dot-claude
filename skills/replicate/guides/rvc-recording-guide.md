# RVC Voice Dataset Recording Guide

Goal: capture 10–30 minutes of clean, solo recordings of your own voice to train an RVC model via `replicate/train-rvc-model`.

## Equipment

- Condenser microphone on a stand (not handheld)
- Audio interface
- Pop filter, 2–4 inches from the capsule
- Closed-back headphones for monitoring
- A quiet room with soft furnishings (couch, rug, curtains, bed). Avoid bathrooms, kitchens, hallways.

## Recording settings

- **48 kHz, mono, 24-bit WAV** (trainer expects 48k)
- Gain so loud passages peak around **-6 dBFS**; normal speech around -18 to -12 dBFS
- Mouth **4–8 inches** from the capsule, slightly off-axis to reduce plosives
- No EQ, no compression, no noise reduction, no reverb — record dry and flat
- One continuous take per block if possible; you can trim later

## Session plan (~20 minutes total)

Do all blocks in one session, same mic position, same gain.

### Block 1 — Conversational speech (5 min)

Read the passages below at a relaxed, natural pace. Don't "perform" — aim for how you'd explain something to a friend.

### Block 2 — Dynamic range (3 min)

Re-read any passage three times:

1. Soft / intimate, as if someone is sleeping nearby
2. Normal conversational
3. Projected, as if talking across a room (not shouting)

### Block 3 — Vocal warm-ups and scales (4 min)

- Lip trills sliding from your lowest to highest comfortable pitch, then back down
- Major scale on "ah" — up one octave and back — at three pitches within your range
- Arpeggios (1-3-5-8-5-3-1) on "oh," "ee," "ay," "oo"
- Sustained notes on each vowel, ~5 seconds each, at a comfortable mid pitch

### Block 4 — Sung melodies (5 min)

Pick two or three of these public-domain songs — they cover a usable range and varied phrasing:

- Amazing Grace
- Shenandoah
- The Water Is Wide
- Scarborough Fair
- Danny Boy
- Early One Morning

Sing a verse or two of each unaccompanied. Don't worry about being pitch-perfect — you want honest timbre, not a polished take.

### Block 5 — Free speech (3 min)

Talk naturally about something familiar — your day, a project you're working on, a movie you watched. This captures your real-world cadence and filler words, which matter for the clone feeling "like you."

---

## Reading passages

### The Rainbow Passage (phonetically balanced, standard speech-testing text)

> When the sunlight strikes raindrops in the air, they act as a prism and form a rainbow. The rainbow is a division of white light into many beautiful colors. These take the shape of a long round arch, with its path high above, and its two ends apparently beyond the horizon. There is, according to legend, a boiling pot of gold at one end. People look, but no one ever finds it. When a man looks for something beyond his reach, his friends say he is looking for the pot of gold at the end of the rainbow.

### Harvard Sentences (IEEE phonetically balanced set — sample of 20)

1. The birch canoe slid on the smooth planks.
2. Glue the sheet to the dark blue background.
3. It's easy to tell the depth of a well.
4. These days a chicken leg is a rare dish.
5. Rice is often served in round bowls.
6. The juice of lemons makes fine punch.
7. The box was thrown beside the parked truck.
8. The hogs were fed chopped corn and garbage.
9. Four hours of steady work faced us.
10. A large size in stockings is hard to sell.
11. The boy was there when the sun rose.
12. A rod is used to catch pink salmon.
13. The source of the huge river is the clear spring.
14. Kick the ball straight and follow through.
15. Help the woman get back to her feet.
16. A pot of tea helps to pass the evening.
17. Smoky fires lack flame and heat.
18. The soft cushion broke the man's fall.
19. The salt breeze came across from the sea.
20. The girl at the booth sold fifty bonds.

### Pangrams and tongue-twisters (for consonant variety)

- The quick brown fox jumps over the lazy dog.
- Pack my box with five dozen liquor jugs.
- How vexingly quick daft zebras jump.
- She sells seashells by the seashore.
- Red leather, yellow leather.
- Unique New York.

---

## After recording

1. **Trim** silence longer than ~1 second, bad takes, coughs, mouse clicks, room noises.
2. **Normalize** the whole session to a consistent level (e.g. -18 LUFS integrated).
3. **Chunk** into 5–15 second segments. Easy ways:
   - Audacity: `Analyze → Silence Finder` or `Sound Finder`, then `File → Export → Export Multiple`
   - ffmpeg: `ffmpeg -i input.wav -f segment -segment_time 10 -c copy split_%03d.wav`
4. **Verify** each chunk is 48 kHz mono WAV, 5–15 seconds, one voice, no silence padding.
5. **Pack** as:
   ```
   dataset_<name>.zip
   └── dataset/
       └── <name>/
           ├── split_0.wav
           ├── split_1.wav
           └── ...
   ```
   The `<name>` is your model identifier (e.g. `dataset_my_voice.zip` → `dataset/my_voice/split_*.wav`).

## Red flags to re-record

- Audible HVAC, fridge, fan, or traffic hum
- Room reverb tail on word endings
- Clipping (visible flat-top peaks)
- Mouth/lip clicks every few seconds (hydrate, step back from mic)
- Heavy breaths between every phrase — edit them out before chunking

## What good data gets you

10 minutes of clean data → a usable clone. 20–30 minutes → noticeably better range and prosody. Past ~30 minutes, returns diminish fast. Don't force more content at the expense of consistency — one great 15-minute session beats a patchy 45-minute one.
