#!/usr/bin/env python3
"""Together text-to-speech (POST /v1/audio/speech, or streaming WebSocket).

Usage (REST, one file at the end):
  tts.py "Hello world" -o out.mp3
      [--model hexgrad/Kokoro-82M] [--voice af_bella] [--format mp3]

Usage (streaming WebSocket, low-latency PCM chunks):
  tts.py "Hello world" -o out.pcm --stream
      [--model hexgrad/Kokoro-82M] [--voice tara]
  # streamed output is raw PCM s16le mono @24kHz:
  #   ffmpeg -f s16le -ar 24000 -ac 1 -i out.pcm out.wav

Embeds model+prompt provenance into REST output (ffmpeg). Auth via TOGETHER_API_KEY.

⚠️ UNTESTED / UNFINISHED: the --stream path is a hand-rolled stdlib WebSocket client
written from the published protocol and has NOT been run against a live key. The REST
path (default) works. Smoke-test --stream before depending on it.
"""
from __future__ import annotations
import argparse, base64, json, os, socket, ssl, sys
from _common import post_json, embed_audio_meta, api_key, die

REST_MODEL = "hexgrad/Kokoro-82M"
HOST = "api.together.ai"


def rest(args):
    audio = post_json("/v1/audio/speech",
                      {"model": args.model, "input": args.prompt,
                       "voice": args.voice, "response_format": args.format},
                      raw=True)
    with open(args.out, "wb") as f:
        f.write(audio)
    embed_audio_meta(args.out, args.model, args.prompt)
    print(args.out)


# ---- minimal stdlib WebSocket client (client frames masked, server unmasked) --

def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed mid-frame")
        buf += chunk
    return buf


def _send_frame(sock, payload: bytes, opcode=0x1):
    header = bytes([0x80 | opcode])  # FIN + opcode
    mask = os.urandom(4)
    n = len(payload)
    if n < 126:
        header += bytes([0x80 | n])
    elif n < 65536:
        header += bytes([0x80 | 126]) + n.to_bytes(2, "big")
    else:
        header += bytes([0x80 | 127]) + n.to_bytes(8, "big")
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    sock.sendall(header + mask + masked)


def _recv_frame(sock):
    b0, b1 = _recv_exact(sock, 2)
    opcode = b0 & 0x0F
    masked = b1 & 0x80
    length = b1 & 0x7F
    if length == 126:
        length = int.from_bytes(_recv_exact(sock, 2), "big")
    elif length == 127:
        length = int.from_bytes(_recv_exact(sock, 8), "big")
    mask = _recv_exact(sock, 4) if masked else None
    payload = _recv_exact(sock, length) if length else b""
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return opcode, payload


def stream(args):
    query = (f"/v1/audio/speech/websocket?model={args.model}"
             f"&voice={args.voice}")
    key = base64.b64encode(os.urandom(16)).decode()
    raw = socket.create_connection((HOST, 443))
    sock = ssl.create_default_context().wrap_socket(raw, server_hostname=HOST)
    handshake = (
        f"GET {query} HTTP/1.1\r\nHost: {HOST}\r\n"
        f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
        f"Authorization: Bearer {api_key()}\r\n\r\n")
    sock.sendall(handshake.encode())

    # read handshake response headers
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += sock.recv(1024)
    if b" 101 " not in resp.split(b"\r\n", 1)[0]:
        die("WebSocket upgrade failed:\n" + resp.decode("utf-8", "replace"))

    _send_frame(sock, json.dumps(
        {"type": "input_text_buffer.append", "text": args.prompt}).encode())
    _send_frame(sock, json.dumps({"type": "input_text_buffer.commit"}).encode())

    msg = b""
    written = 0
    with open(args.out, "wb") as f:
        while True:
            opcode, payload = _recv_frame(sock)
            if opcode == 0x8:                       # close
                break
            if opcode == 0x9:                       # ping -> pong
                _send_frame(sock, payload, opcode=0xA)
                continue
            msg += payload
            if opcode == 0x0 and not payload:       # (defensive) keep assembling
                continue
            try:
                evt = json.loads(msg)
            except json.JSONDecodeError:
                continue                            # fragmented; wait for more
            msg = b""
            t = evt.get("type", "")
            if t == "conversation.item.audio_output.delta":
                f.write(base64.b64decode(evt["delta"]))
                written += 1
            elif t == "conversation.item.audio_output.done":
                break
            elif t == "conversation.item.tts.failed":
                die(f"TTS failed: {evt.get('error')}")
    sock.close()
    print(f"{args.out} ({written} chunks, raw PCM s16le mono @24kHz)",
          file=sys.stderr)
    print(args.out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--model", default=REST_MODEL)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--format", default="mp3", help="REST only: mp3/wav/raw/mulaw")
    ap.add_argument("--stream", action="store_true",
                    help="use the streaming WebSocket (raw PCM output)")
    args = ap.parse_args()
    if args.voice is None:
        args.voice = "tara" if args.stream else "af_bella"
    (stream if args.stream else rest)(args)


if __name__ == "__main__":
    main()
