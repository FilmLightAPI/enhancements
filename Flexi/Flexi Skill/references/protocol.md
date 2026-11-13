# Flexi protocol

The full overview ships as `doc/FlexiEffects.md`; message and reply formats are in
`etc/flexi_message_v1.schema` and `etc/flexi_reply_v1.schema`. This is the short form, with what
the host actually does.

## Discovery and launch

- Baselight reads `.flexi` manifests in the Flexi directory. Installed effects live one per
  folder, exactly one level down: `<flexi dir>/effects/<dir>/<name>.flexi`. A `.flexi` directly in
  `<flexi dir>` describes an effect that may not be installed yet.
- To start an effect, Baselight runs the manifest's `launch_command` with that folder as the
  working directory. One process runs per GPU per render process, so a multi-GPU machine runs
  several copies of the effect at once.
- The effect must connect within 30 seconds, and stay running (or start a process that does).
- Environment:

| Variable | Meaning |
|---|---|
| `FLEXI_SERVER_URL` | Websocket URL to connect to. Must be used. |
| `INSTALL_DIR` | The Baselight install, to run its command-line tools |
| `FLEXI_CUDA_GPU_ID`, `CUDA_VISIBLE_DEVICES` | Linux: the one GPU the effect may use |
| `FLEXI_METAL_DEVICE_INDEX` | macOS: the one Metal device the effect may use |
| `LD_LIBRARY_PATH` | Linux: includes the effect's and the platform's `lib/` |

Baselight started from the Dock or a service does not have your shell's `PATH`.

## Methods, in typical order

| Method | Purpose | GPU allowed | Notes |
|---|---|---|---|
| `describe_effect_v1` | Process mode, inputs, outputs, params, UI | No | Fast. Cached until the `.flexi` changes or Baselight restarts. |
| `query_input_rects_v1` | Input area needed for an output area | No | Only if listed in `supported_methods` (or `local_methods`); otherwise each input covers the output's area. Cached. See `references/geometry.md` |
| `query_output_rect_v1` | Output area producible from the inputs | No | As above |
| `query_vram_requirement_v1` | `min_mb`, `max_mb` for these params and size | No | Both values required. Cached. |
| `set_vram_limit_v1` | How much VRAM the effect may use | Yes, after it | Reply only once usage ≤ limit, or reply and exit (`'quit'`) |
| `run_generate_v1` | Render one frame | Yes | One caller at a time per process |
| `test_effect_v1` | Optional self-test, used by `fl-flexi check --full` | Yes | List it in `supported_methods` |
| `shutdown_v1` | Reply, release everything, exit | — | `effect` may be null |

Every message gets exactly one reply: the message's `effect`, its integer `id`, the method in
capitals, and `data` and/or `log`.

## Timeouts

Apart from the 30-second connection wait, Baselight waits for every reply indefinitely. It warns
when a reply takes more than two seconds. So a slow `describe_effect` or query stalls the user's
session, and a reply Baselight cannot match to a message (not a JSON object, or without the
integer `id`) leaves it waiting forever.

## Caching and local methods

Replies to `query_input_rects_v1`, `query_output_rect_v1` and `query_vram_requirement_v1` are
cached per effect process, assuming the same message always gets the same reply. The cache goes
when the process restarts. Baselight also caches error replies, and keys the cache on the
message only, not the effect: when one process serves several effects, give them identical
answers to identical queries, or give each effect its own process (its own `launch_command`).

All three can instead be answered inside Baselight, with no round trip, from a `local_methods`
object in the `describe_effect` reply. The words `'output'` and `'src:0'` are literal keys of the
message, not your output's name:

```python
'local_methods': {
    'query_vram_requirement_v1': 3000,               # min_mb = max_mb = 3000
    'query_input_rects_v1': {
        'src': ['output', 16],                       # the output rect grown by 16 pixels
        'src2': ['output', 'radius'],                # grown by the value of the 'radius' param
        'matte': 'output',                           # the output rect itself
        'ref': {'rect': {'left': 0, 'top': 0, 'width': 256, 'height': 256}},   # a fixed rect
    },
    'query_output_rect_v1': {'output': ['src:0', -5]},   # the src:0 rect shrunk by 5 pixels
}
```

## Logging

Any reply may include `log`: a list of `{level, message, detail}`, levels as syslog: 0 fatal,
3 error, 4 warning, 6 info, 7 debug. Level 3 or lower fails the call and shows the message to
the user. Other levels are only written to the log.

Everything the effect prints, and every log entry, appears in the output of the Baselight process
that launched it, prefixed `Flexi <identifier> v<version>:`. Libraries that print start-up
messages to stderr (TensorFlow Lite, MediaPipe, ONNX Runtime and others) fill that log on every
launch: turn their logging down in the effect.

## Process modes

| Mode | Platform | Notes |
|---|---|---|
| `cuda_ipc` | Linux | Zero-copy CUDA device buffers |
| `shm` | macOS (and Linux) | POSIX shared memory, 32-bit float pixels |
| `file` | Any | Image files in `process_filetype` (`PPM16`, `TIFF16`, `EXR`, …). Slowest; for languages without shared memory or CUDA. |

Give a mode per OS: `'process_mode': {'linux': 'cuda_ipc', 'macos': 'shm'}`. Both keys are
needed; Intel Macs use `macos`.
