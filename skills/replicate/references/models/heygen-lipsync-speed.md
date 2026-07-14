# heygen/lipsync-speed

Model page: https://replicate.com/heygen/lipsync-speed

Audio-driven lip synchronization: takes a source video of a speaker plus a replacement audio track and re-animates the speaker's mouth to match the new audio. Optimized for speed over pixel-perfect accuracy — for higher quality, use `heygen/lipsync-precision`.

## Use cases

- Cross-language dubbing
- Voiceover replacement
- Content localization
- Audio correction / ADR

## Input schema

| Field                       | Type         | Required | Default | Description                                                                                |
| --------------------------- | ------------ | -------- | ------- | ------------------------------------------------------------------------------------------ |
| `video`                     | string (URI) | ✅       | —       | Source video file to lip-sync.                                                             |
| `audio`                     | string (URI) | ✅       | —       | Replacement audio file. The video's lip movements will be re-animated to match this audio. |
| `enable_dynamic_duration`   | boolean      |          | `true`  | Allow the output duration to adjust to match the new audio length.                         |
| `disable_music_track`       | boolean      |          | `false` | Strip background music from the source video.                                              |
| `enable_speech_enhancement` | boolean      |          | `false` | Enhance speech quality in the output.                                                      |

Both `video` and `audio` accept an HTTPS URL or a local file path (our `run_model.py` auto-uploads local files).

## Output

A single URI to the lipsynced video (MP4). `run_model.py` will save it as `heygen_lipsync-speed_0.mp4` in the output directory.

## Pricing

**$0.0333 per second of output video.** A 60-second output runs ~$2.00. Dynamic duration means the output length tracks the audio, so estimate cost against the audio's duration when that flag is on.

## Example

```bash
python scripts/run_model.py heygen/lipsync-speed \
    --input '{
      "video": "https://example.com/speaker.mp4",
      "audio": "./voiceover-es.wav",
      "enable_dynamic_duration": true,
      "enable_speech_enhancement": true
    }' \
    --output ./out/
```

Local-file variant (both inputs local):

```bash
python scripts/run_model.py heygen/lipsync-speed \
    --input '{
      "video": "./source.mp4",
      "audio": "./new-audio.wav"
    }' \
    --output ./out/
```

## Picking speed vs. precision

- `heygen/lipsync-speed` — fast, audio-only analysis, cheaper. Use for drafts, bulk dubbing, and anything under close-up scrutiny where minor artifacts are acceptable.
- `heygen/lipsync-precision` — slower and more expensive, sharper mouth shapes. Use for hero shots, marketing content, or any close-up where lip detail matters.

Default to `speed` and only upgrade if the output isn't good enough.
