# OpenRouter — vision (multimodal chat)

Pass images in `messages[].content` as a list mixing `text` and `image_url` blocks. A public URL or a `data:image/...;base64,...` data URI both work — same OpenAI format.

```bash
curl -sS https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.5-flash-lite",
    "messages": [{
      "role":"user",
      "content":[
        {"type":"text","text":"Describe this image."},
        {"type":"image_url","image_url":{"url":"https://example.com/img.png"}}
      ]
    }]
  }' | jq -r '.choices[0].message.content'
```

## Base64 (local file)

```bash
B64=$(base64 -i photo.jpg)   # macOS; use base64 -w0 on Linux
curl -sS https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"google/gemini-2.5-flash-lite\",\"messages\":[{\"role\":\"user\",\"content\":[
        {\"type\":\"text\",\"text\":\"What is in this image?\"},
        {\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/jpeg;base64,$B64\"}}]}]}" \
  | jq -r '.choices[0].message.content'
```

## Picking a vision model

Filter for image input support:

```bash
curl -sS https://openrouter.ai/api/v1/models \
  | jq -r '.data[] | select(.architecture.input_modalities|index("image")) | .id' | head
```

Reliable, cheap options at last check: `google/gemini-2.5-flash-lite`, `qwen/qwen3-vl-235b-a22b-instruct`, plus the Claude and GPT-5 families. Image tokens bill at the model's input rate; large images cost more, so downscale when full resolution isn't needed.

## PDFs

Some models accept PDFs via a `file` content block (`{"type":"file","file":{"filename":"doc.pdf","file_data":"data:application/pdf;base64,..."}}`); OpenRouter can also OCR them. Check the model's `input_modalities` for `"file"` first.
