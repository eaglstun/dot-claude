# Together — embeddings (and rerank)

> **Script:** `scripts/embeddings.py "a" "b" [--input-file f] [--out f]` wraps this endpoint.

## Embeddings

Endpoint: `POST https://api.together.ai/v1/embeddings`. `input` accepts a single string or an array.

```bash
curl -sS https://api.together.ai/v1/embeddings \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "intfloat/multilingual-e5-large-instruct",
    "input": ["first chunk", "second chunk"]
  }' | jq '.data[].embedding | length'
```

Response: `.data[].embedding` is a float array per input.

### Serverless models

| Model                                     | dim  | ctx | $/M tokens |
| ----------------------------------------- | ---- | --- | ---------- |
| `intfloat/multilingual-e5-large-instruct` | 1024 | 514 | $0.02      |

**Only one embedding model is currently serverless on Together.** The BGE / M2-BERT / Arctic models the docs reference all require dedicated endpoints. For most RAG work this one model is fine — 1024 dim, multilingual, ~$0.02 per million tokens. If you need higher-dim embeddings or domain-specific tuning, use OpenAI / Voyage / Cohere rather than standing up a dedicated endpoint.

## Rerank — not serverless

`/v1/rerank` exists in the API surface but **all rerank models (`mixedbread-ai/mxbai-rerank-large-v2`, `Salesforce/Llama-Rank-V1`) are dedicated-endpoint only** from this account. Calling them returns `non-serverless`.

For lightweight rerank without standing up a dedicated endpoint:

- Use the embedding model above + cosine similarity for top-k selection
- Or call Cohere's hosted rerank API
