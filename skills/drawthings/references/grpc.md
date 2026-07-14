# Draw Things gRPC interface (the headless full-control path)

Source: `Libraries/GRPC/Models/Sources/imageService/imageService.proto` in
[draw-things-community](https://github.com/drawthingsai/draw-things-community). This is
the native protocol the app uses to offload to remote compute, and what the
[ComfyUI bridge](https://github.com/drawthingsai/draw-things-comfyui) and
[MediaGenerationKit](https://github.com/drawthingsai/media-generation-kit) speak.

**Bottom line:** gRPC has **first-class `mask` and `hints` fields** that the HTTP API and
the CLI lack. That single fact explains the entire control investigation — inpaint and the
preprocessed/reference controls work over gRPC precisely because the protocol carries the
mask and the control hint tensors. They fail over HTTP/CLI because those interfaces have
nowhere to put them.

## Services

- **`ImageGenerationService`** — the generation plane.
  - `GenerateImage(ImageGenerationRequest) → stream ImageGenerationResponse`
  - `FilesExist`, `UploadFile` (chunked), `Echo`, `Pubkey`, `Hours` — file sync + auth/handshake.
- **`ControlPanelService`** — server **admin** plane, not generation: `ManageGPUServer`,
  `UpdateThrottlingConfig`, `UpdateModelList`, `UpdateSharedSecret`, `UpdatePrivateKey`,
  `UpdateComputeUnit`. (Only relevant if you run your own gRPC compute server.)

## `ImageGenerationRequest` — the key message

| Field                                                               | #     | Meaning                                                                                                                            |
| ------------------------------------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `image`                                                             | 1     | init image (sha256 content-addressed)                                                                                              |
| **`mask`**                                                          | 3     | **inpaint mask** — first-class. The thing HTTP rejected (`Unrecognized keys: ["mask"]`) and the CLI couldn't supply                |
| **`hints`**                                                         | 4     | `repeated HintProto` — **the control-input channel** (depth maps, pose skeletons, scribbles, shuffle/reference)                    |
| `prompt` / `negativePrompt`                                         | 5 / 6 | text                                                                                                                               |
| `configuration`                                                     | 7     | **FlatBuffer-encoded** full config (the `JSGenerationConfiguration`: controls, loras, `preserveOriginalAfterInpaint`, steps, etc.) |
| `contents`                                                          | 12    | content-addressable blob store — images/tensors referenced by sha256                                                               |
| `override`, `keywords`, `user`, `device`, `sharedSecret`, `chunked` | 8–14  | metadata override, auth, chunking                                                                                                  |

```proto
message HintProto {
  string hintType = 1;                  // which control input: depth / pose / scribble / shuffle(moodboard) / ...
  repeated TensorAndWeight tensors = 2; // the (already-preprocessed) control tensor(s) + weight
}
message TensorAndWeight { bytes tensor = 1; float weight = 2; }  // tensor is sha256 content
```

`ImageGenerationResponse` is **streamed**: `generatedImages`, a live `previewImage`,
`signposts` (per-step progress: textEncoded → sampling → decoded → upscaled…), chunked
transfer, and even `generatedAudio`.

## Why this is the answer — and the catch

It confirms the capability ladder from the control battery (`../output/results.md`):

- **HTTP API**: `image` + `prompt` + `configuration` only; auto-extracts depth. No mask, no hints.
- **CLI**: config (JSON) + `--image`; still no mask, no hints.
- **gRPC**: `mask` **and** `hints` first-class → inpaint + every preprocessed/reference control.

**But gRPC is real work, for two reasons the proto makes explicit:**

1. **`configuration` is a FlatBuffer, not JSON.** You need the FlatBuffer schema (in the
   repo) and a `flatc`-generated encoder. Hand-building the request is non-trivial.
2. **`hints` are _pre-processed_ tensors.** The protocol carries a depth map / pose
   skeleton / reference embedding — it does **not** extract them for you. You (or a client
   lib) still run the preprocessing, then content-address the tensor (sha256) and attach it
   with the right `hintType`. Plus a content-addressable upload layer (`UploadFile` /
   `FilesExist` / `contents`) and `sharedSecret` auth.

## Practical guidance

- **Don't hand-roll raw gRPC** for this skill. Use a client that encodes the FlatBuffer and
  manages hints/CAS: **MediaGenerationKit** (Swift) or the **draw-things-comfyui** bridge
  (TypeScript). (Note: MediaGenerationKit currently has open build issues — see
  [`ecosystem.md`](ecosystem.md).)
- For headless scripting from Python/CLI, the pragmatic paths remain: **`draw-things-cli`**
  for txt2img/img2img/depth/PuLID/video/training, and the **in-app Scripts** JS API for
  mask/moodboard/preprocessed controls. gRPC is the "full control, headless, but build a
  real client" option.
- To enable a gRPC server: app → API Server → **Protocol: gRPC** (+ "Enable Model
  Browser"), or run `gRPCServerCLI` from draw-things-community.
