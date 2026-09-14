# Together — vision (multimodal chat)

> **Script:** `scripts/vision.py "prompt" --image URL_or_path` wraps this (local files become data URLs).

Pass images inline in `messages[].content` as a list mixing `text` and `image_url` blocks. URL or `data:image/...;base64,...` both work.

```bash
curl -sS https://api.together.ai/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-Vision-Free",
    "messages": [{
      "role":"user",
      "content":[
        {"type":"text","text":"Describe this image."},
        {"type":"image_url","image_url":{"url":"https://example.com/img.png"}}
      ]
    }]
  }' | jq -r '.choices[0].message.content'
```

## Image token billing

Images bill as input tokens by tile grid: **1,601 tokens per 560×560 tile**, capped at 2×2 (6,404 tokens) per image.

| Dimensions    | Tiles | Tokens |
| ------------- | ----- | ------ |
| ≤559×559      | 1×1   | 1,601  |
| ≤559H, >560W  | 1×2   | 3,202  |
| >560H, ≤559W  | 2×1   | 3,202  |
| >560H & >560W | 2×2   | 6,404  |

## Picking a vision model

Vision-capable serverless models shift around. Test before adding to a chain using the snippet in `references/serverless.md` (`"choices"` = serverless, `"non-serverless"` = dedicated only). Llama Vision and recent Qwen-VL turbos have generally been callable. Pricing follows the underlying chat model's `$/M in` rate (see `chat.md`) applied to text + image tokens.
