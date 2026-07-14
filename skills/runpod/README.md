# runpod

Claude Code skill for deploying local **Ollama** models (fine-tunes / quantizations) to **Runpod Serverless**. Two complementary paths, both driven by scripts under `scripts/`. For stock public models, use a hosted provider (Together, Groq, Replicate) instead — these scripts only pay off for models you control.

## Pick the deploy path

| Path                           | Script                          | When                                                                |
| ------------------------------ | ------------------------------- | ------------------------------------------------------------------- |
| Bake model into a Docker image | `scripts/runpod-deploy.sh`      | One-off model, no volume yet; OK with ~15GB image + slow cold start |
| Sync to a network volume (S3)  | `scripts/runpod-volume-sync.sh` | Multiple models / frequent iteration; slim image, faster boots      |

## Usage

```bash
# Path 1 — build + push image to Docker Hub
DOCKER_USER=<user> ./scripts/runpod-deploy.sh [model-name] [tag]

# Path 2 — mirror models to the Runpod S3 volume
./scripts/runpod-volume-sync.sh mote-14b-q3-ft margot-1.7b-q8-ft
```

**Prereqs:** Path 1 needs `ollama` + `docker` (logged in) and the model present locally; Path 2 needs `awscli` + `jq` and an AWS profile `runpod` holding Runpod's S3 credentials. See `SKILL.md` for endpoint config, env overrides, and verification commands.

After deploy, the endpoint URL is wired into openclaw by hand — see the `openclaw-api` skill.
