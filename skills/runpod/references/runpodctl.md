# runpodctl — the Runpod CLI

Official open-source CLI for managing Runpod resources from the command line, as an alternative to hand-rolled `curl` calls against `references/api/`. Same account, same underlying REST API — this just wraps it.

**On this machine:** already installed via Homebrew (`runpodctl 2.8.0`) and already authenticated — `runpodctl pod list` works with no extra setup, picking up credentials from the existing `RUNPOD_API_KEY` env var. Verified 2026-07-30.

## Install (if starting fresh elsewhere)

```bash
# macOS (Homebrew)
brew install runpod/runpodctl/runpodctl

# macOS/Linux (script installer — installs to /usr/local/bin as root, ~/.local/bin otherwise)
bash <(curl -sL cli.runpod.io)

# Windows: direct .exe download from the releases page
# Also available via conda-forge, and preinstalled in some Runpod container images
```

## Auth

```bash
runpodctl doctor              # interactive first-time setup: API key + SSH key + verification (recommended)
runpodctl config --apiKey YOUR_API_KEY   # manual, non-interactive
runpodctl config --apiUrl ...            # override API endpoint, default https://api.runpod.io/graphql — leave alone normally
```

## Command groups

All commands support `--help`. `<id>` placeholders below use whatever the list/get command actually returns (pod id, endpoint id, template id, volume id).

### `pod` — GPU Pods

```bash
runpodctl pod list [--all] [--status <s>] [--name <n>]        # filters: --status, --since, --created-after, --compute-type, --name
runpodctl pod get <pod-id>
runpodctl pod create --image "runpod/pytorch:..." --gpu-id "NVIDIA GeForce RTX 4090"
  # other create flags: --template-id, --name, --gpu-count, --compute-type, --container-disk-in-gb,
  #                      --volume-in-gb, --ports, --env, --cloud-type, --stop-after, --terminate-after
runpodctl pod start|stop|restart|reset <pod-id>
runpodctl pod update <pod-id> [--name] [--image] [--container-disk-in-gb] [--volume-in-gb] [--ports] [--env]
runpodctl pod delete <pod-id>
```

### `serverless` (alias `sls`) — Serverless endpoints

```bash
runpodctl serverless list [--include-template] [--include-workers]
runpodctl serverless get <endpoint-id> [--include-template] [--include-workers]
runpodctl serverless create --template-id <tpl-id> --gpu-id "NVIDIA GeForce RTX 4090" --workers-max 5
  # alt to --template-id: --hub-id (deploy straight from Runpod Hub, see `hub` below)
  # other flags: --name (min 3 chars), --compute-type (GPU|CPU, default GPU), --workers-min, --model-reference (HF URL)
runpodctl serverless update <endpoint-id> [--workers-min] [--workers-max] [--idle-timeout] [--execution-timeout] [--template-id] [--name]
runpodctl serverless delete <endpoint-id>
```

Same `workersMin:0` caveat applies here as the raw REST API — see the cost gotcha in `api/control-plane.md`. `runpodctl serverless get <id> --include-workers` is a faster way to eyeball whether a worker crept back up than hitting the data-plane `/health` endpoint by hand.

### `template`

```bash
runpodctl template list [--type official|community|user] [--limit 10] [--all]
runpodctl template search <name> [--type ...] [--limit] [--offset]
runpodctl template get <template-id>
runpodctl template create --name "my-template" --image "runpod/pytorch:..." [--volume-in-gb] [--ports] [--env '<json>'] [--serverless]
runpodctl template update <template-id> [--name] [--image] [--ports] [--env] [--readme]
runpodctl template delete <template-id>
```

**Cross-reference:** `template create --serverless` is the CLI's version of the undocumented `"isServerless": true` field needed when creating a serverless template via raw REST (`api/control-plane.md`) — confirms that flag is a real, deliberate (if poorly-documented) distinction, not a fluke of the REST API.

### `hub` — Runpod Hub marketplace (public endpoint/pod templates)

```bash
runpodctl hub list [--deployment-type POD|SERVERLESS] [--category ...] [--owner ...] [--sort stars|deploys|created|released|updated|views] [--limit] [--offset]
runpodctl hub search <query> [same filters]
runpodctl hub get <listing-id | owner/name>
```

Once you've found a listing, deploy it directly: `runpodctl serverless create --hub-id <id>` — inherits the Hub release's GPU/storage config, GPU overridable.

### `network-volume` (alias `nv`)

```bash
runpodctl network-volume list
runpodctl network-volume get <volume-id>
runpodctl network-volume create --name "my-volume" --size 100 --data-center-id "US-GA-1"   # size in GB, 1-4000
runpodctl network-volume update <volume-id> [--name] [--size <must exceed current>]
runpodctl network-volume delete <volume-id>
```

### `gpu` — list GPU types + live pricing (fills a real gap in the REST API)

```bash
runpodctl gpu list [--include-unavailable]
```

The REST control plane has **no** `GET /v1/gputypes` route (confirmed 400 in `api/gpu-types.md`) — this is the actual authoritative, live source for both the exact `gpuId` string to use as `gpuTypeIds` in REST/template calls, and current pricing. Verified live 2026-07-30 (Pod/community+secure cloud pricing, **not** confirmed identical to serverless per-second billing — treat as a strong proxy, not a guarantee):

| GPU (`gpuId`)             | Community $/hr            | Secure $/hr |
| ------------------------- | ------------------------- | ----------- |
| `NVIDIA RTX A4000`        | 0.17                      | 0.25        |
| `NVIDIA RTX A6000`        | 0.33                      | 0.53        |
| `NVIDIA GeForce RTX 4090` | 0.34                      | 0.69        |
| `NVIDIA L4`               | — (community unavailable) | 0.39        |
| `NVIDIA A40`              | — (community unavailable) | 0.44        |
| `NVIDIA L40S`             | 0.79                      | 0.99        |

Each entry also has `dataCenterAvailability` (per-datacenter `stockStatus`) — worth checking before assuming a GPU is actually schedulable somewhere.

### `send` / `receive` — peer-to-peer file transfer (e.g. to/from a Pod)

```bash
runpodctl send ./my-dataset --code rainbow-unicorn-42    # on the sending machine
runpodctl receive rainbow-unicorn-42                     # on the receiving machine (e.g. inside a Pod's terminal)
```

Both sides need the same `--code`/code phrase. Undocumented on the doc page: size limits, transfer speed, session expiry, and resume-on-interrupt behavior — treat as unverified until tested.

### `ssh`

```bash
runpodctl ssh info <pod-id> [-v]           # prints connection details, does NOT open a session itself
runpodctl ssh list-keys
runpodctl ssh add-key --key-file ~/.ssh/id_ed25519.pub   # or --key "<raw pubkey>"
runpodctl ssh remove-key <name-or-fingerprint>           # use fingerprint if multiple keys share a name
```

`info` gives you the pieces (`user@host`, `-p <port>`, `-i <key-path>`) — you then run the actual `ssh ...` command yourself.

### Smaller/utility groups (not deep-dived — one-liners from the doc)

- `runpodctl datacenter` (alias `dc`) — list/inspect datacenters (availability context for `pod create`/`gpu list`).
- `runpodctl billing` — account billing history.
- `runpodctl user` (alias `me`) — current account details.
- `runpodctl version` / `runpodctl update` — CLI version info / self-update.
- `runpodctl registry` — manage container registry credentials (for private images on templates).

## Sources

docs.runpod.io: `/runpodctl/overview`, `/runpodctl/reference/runpodctl-{config,doctor,pod,serverless,template,hub,network-volume,gpu,send,receive,ssh}`. GPU pricing table and pod/serverless/network-volume emptiness cross-checked live against this account 2026-07-30 (consistent with the REST API state after the cleanup in `api/control-plane.md`).
