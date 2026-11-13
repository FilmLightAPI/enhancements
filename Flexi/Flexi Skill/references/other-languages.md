# Effects in other languages

Flexi is a protocol, not a Python library. An effect can be any program that can:

1. read `FLEXI_SERVER_URL` from its environment and open a websocket to it,
2. read JSON messages and send JSON replies,
3. read and write the images.

`flexi.py` does all three for Python. In any other language, implement them directly from
`doc/FlexiEffects.md` and the schemas in `etc/`. `examples/cpp-invert` is a complete effect in
C++, using shared memory, with a minimal WebSocket client. To run an existing program on each
frame, a small Python effect that calls it (`examples/run-tool`) is usually simpler than speaking
the protocol from that program.

## Messages and replies

Each message has `effect` (`[identifier, version]` or `[identifier, version, instance]`), `id`,
`method` and `data`. Messages may arrive as a JSON array of several. Reply to each one:

```json
{"effect": ["com.example.x", 1], "id": 7, "method": "RUN_GENERATE_V1", "data": {}}
```

- `method` is the message's method in capitals.
- Put results in `data`. To report a problem add `log`:
  `[{"level": 3, "message": "Model not found", "detail": "…"}]` (3 error, 4 warning, 6 info,
  7 debug). Error levels fail the call and show to the user.
- Always reply with a JSON object carrying the message's integer `id`. Baselight waits
  forever for a reply it cannot match.
- `shutdown_v1` may arrive with `effect` null: reply, close the socket, exit.
- `set_vram_limit_v1`: reply only once your GPU use is within `data.limit_mb`, or reply and exit.

## Images as files

With `process_mode` `file` no shared memory or CUDA is needed:

```json
"process_mode": "file",
"process_filetype": "PPM16"
```

Each input entry carries `file`, a path to an image Baselight wrote, and the output entry names
the file to write. `PPM16` is uncompressed and needs no image library (`PGM` too, for one 8-bit channel); `TIFF16`,
`PNG16`, `EXR` and the other types `bl-render -list` shows suit languages with good image
libraries. Files are slower than shared memory: prefer `shm` (macOS) or `cuda_ipc` (Linux) when
your language can use them.

## Shared memory and CUDA

- `shm`: the entry's `shm` is a POSIX shared-memory name (`/…`); map it read/write. Pixels are
  32-bit floats, interleaved unless the input or output declared `planar`.
- `cuda_ipc` (Linux): `cuda_ipc` is a hex-encoded 64-byte `cudaIpcMemHandle_t`; open it with
  `cudaIpcOpenMemHandle` in the GPU named by `FLEXI_CUDA_GPU_ID`. Synchronise before replying.
- Each entry's `rect` gives the area the buffer covers, as `{"left", "top", "width", "height"}`
  in pixels. The output rect can differ from the input's: index each buffer by its own rect.

## Running it

The launch command runs with a minimal environment: Baselight started from the Dock does not have
your shell's `PATH`. Ship the runtime with the effect, or have a small launch script look for it
in known places, and say in your installation notes what
must be installed on every machine that renders.
