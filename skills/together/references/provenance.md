# Together — media provenance (required)

When this skill generates an image, video, or audio file, **the model slug and prompt MUST be embedded into the output file** before reporting the path back. Naked bytes are not acceptable.

The `scripts/` helpers (`images.py`, `tts.py`, `video.py`) do this automatically via `scripts/_common.py`. If you call the API directly with `curl`, embed it yourself:

- **Images / video** (JPG/PNG/WebP/MP4/MOV):
  `exiftool -overwrite_original -Comment="$PROMPT" -Description="$PROMPT" -UserComment="$PROMPT" -XMP-dc:Description="$PROMPT" -Software="together/$MODEL" <file>`
- **Audio** (WAV/MP3/FLAC):
  `ffmpeg -i raw.wav -metadata comment="model=$MODEL; prompt=$PROMPT" -c copy out.wav`

Verify with `exiftool -Comment -Description <file>` for media, `ffprobe -show_format <file>` for audio. If `exiftool` is missing, `brew install exiftool`.
