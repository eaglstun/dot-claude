# zsxkib/multitalk

Model page: https://replicate.com/zsxkib/multitalk

**Audio-driven multi-person conversational video.** Takes a single reference image containing one or two people, plus an audio track for each person, and produces a video where each subject lip-syncs their respective audio — with the model handling interaction dynamics (turn-taking, reactions, eye contact) between them.

Think "podcast-style two-shot from a still photo + two voiceovers" rather than a single talking head.

## Input schema

| Field            | Type         | Required | Default                                                                                                  | Description                                                                                 |
| ---------------- | ------------ | -------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `image`          | string (URI) | ✅       | —                                                                                                        | Reference image containing the person(s).                                                   |
| `first_audio`    | string (URI) | ✅       | —                                                                                                        | Audio track driving person 1.                                                               |
| `second_audio`   | string (URI) |          | —                                                                                                        | Audio track for person 2. Omit for a single-person talking head.                            |
| `prompt`         | string       |          | `"A smiling man and woman wearing headphones sit in front of microphones, appearing to host a podcast."` | Describes the scene/interaction.                                                            |
| `num_frames`     | integer      |          | `81`                                                                                                     | Range 25–201. Auto-rounded to form `4n+1` (e.g. 81, 85, ..., 201).                          |
| `sampling_steps` | integer      |          | `40`                                                                                                     | Range 2–100. Higher = better quality, slower.                                               |
| `turbo`          | boolean      |          | `true`                                                                                                   | Speed optimizations (adjusted thresholds / guidance). Leave on unless you need max quality. |
| `seed`           | integer      |          | random                                                                                                   | For reproducibility.                                                                        |

Local `image`, `first_audio`, `second_audio` paths are auto-uploaded by `run_model.py`.

## Output

A single URI to the generated video (MP4). Saved as `zsxkib_multitalk_0.mp4`.

## Frame-count math

Output duration depends on the internal frame rate. The `num_frames` constraint (25–201, snapped to `4n+1`) gives you roughly:

| `num_frames` | Typical duration |
| ------------ | ---------------- |
| 25           | ~1s              |
| 81 (default) | ~3–4s            |
| 121          | ~5s              |
| 201 (max)    | ~8s              |

For longer conversations, run multiple passes with continuous audio segments and concatenate in post.

## Pricing and runtime

- **~$0.59 per run** (≈ 1 generation per $1)
- **~7 minutes** typical runtime
- 14B-parameter diffusion transformer on a 24GB+ NVIDIA GPU

## Examples

**Two-person podcast from a photo:**

```bash
python scripts/run_model.py zsxkib/multitalk \
    --input '{
      "image": "./two_hosts_at_mics.jpg",
      "first_audio": "./host_a.wav",
      "second_audio": "./host_b.wav",
      "prompt": "two podcast hosts having a lively discussion, making eye contact, natural gestures",
      "num_frames": 121
    }' \
    --output ./out/
```

**Single-person talking head** (just omit `second_audio`):

```bash
python scripts/run_model.py zsxkib/multitalk \
    --input '{
      "image": "./portrait.jpg",
      "first_audio": "./monologue.wav",
      "prompt": "a confident presenter speaking directly to the camera in a well-lit studio",
      "num_frames": 81
    }' \
    --output ./out/
```

**Higher-quality pass (turbo off, more steps):**

```bash
python scripts/run_model.py zsxkib/multitalk \
    --input '{
      "image": "./portrait.jpg",
      "first_audio": "./voice.wav",
      "turbo": false,
      "sampling_steps": 80,
      "num_frames": 81
    }' \
    --output ./out/
```

## Tips

- **Clear reference image.** Both subjects visible, well-lit, faces not occluded, neutral expressions. A clean two-shot produces cleaner results than a busy candid.
- **Clean audio.** Dialogue over music or noise degrades lipsync quality. Denoise before passing in.
- **Match audio lengths.** For two-person convos, either make the two tracks the same length (silence-pad the shorter one) or accept that the shorter person will just be quiet in the final frames.
- **Prompt the _interaction_, not the people.** Describe the scenario ("lively debate", "thoughtful interview", "casual chat over coffee"). The model uses this for body language and attention cues.
- **Start with defaults** (`turbo: true`, `sampling_steps: 40`). Only turn turbo off if you're unhappy with the result.

## Gotchas

- **Max 2 people.** Three-person panels, crowds, or group shots are unsupported — pick a different model or cut to two-shots.
- **`num_frames` snaps to 4n+1.** 100 will become 101; 80 will become 81. Don't over-specify.
- **~8s hard cap.** For longer content, segment the audio and concat the outputs.
- **Complex interactions get misinterpreted.** Subtle reactions, sarcasm, or dense back-and-forth may produce weird facial expressions. Keep scripts direct for best results.
