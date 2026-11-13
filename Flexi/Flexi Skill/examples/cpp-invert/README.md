# Example Invert (C++)

A Flexi effect as a compiled program: no Python, no Flexi platform. It inverts the image, with a
mix slider.

- `flexi_invert.cpp` speaks the protocol directly: it connects to `FLEXI_SERVER_URL` with a small
  WebSocket client, answers each JSON message, and replies with the method name in capitals and
  the message's `id`.
- `process_mode: shm` on macOS and Linux: each image is a POSIX shared-memory buffer of 32-bit
  float RGB pixels, which the effect maps with `shm_open` and `mmap`. The host creates and removes
  the buffers; the effect never unlinks them.
- Each buffer covers its own `rect` (`left`, `top`, `width`, `height`): the output pixel at
  `(x, y)` reads the input at `(out.left + x - in.left, out.top + y - in.top)`.
- It handles one message at a time, so Baselight's other messages wait while a frame renders.
  That is fine for a fast effect; a slow one should answer `describe_effect_v1` and the queries
  from another thread, because Baselight expects those replies at once.
- `build.sh` builds `flexi_invert` with the system compiler. It downloads one header,
  [nlohmann/json](https://github.com/nlohmann/json) (MIT), pinned by checksum.
- The manifest installs the built binary and launches it as `./flexi_invert`. No
  `flexi_platform`: there is no Python venv to build.

## Building

```bash
./build.sh
fl-install-flexi-effect -t ~/flexi-scratch com.example.cpp_invert.v1.flexi
```

- **macOS**: `build.sh` makes one universal binary that runs on Apple silicon and Intel Macs
  (`lipo -archs flexi_invert` shows `x86_64 arm64`). Build it on any Mac.
- **Linux**: a binary needs the glibc it was built against or newer. Build on the oldest
  distribution your users run: a binary built on Ubuntu 22.04 needs glibc 2.34 and will not start
  on Rocky Linux 8 (2.28). `build.sh` links the C++ runtime statically, so glibc is the only
  system library it needs (`ldd flexi_invert`).

Shipping it, signing it for macOS and bundling libraries: see "Native binaries" in
`references/distribution.md`.

## Testing

```bash
"<flexi dir>/platforms/<platform>/bin/python3" <app>/share/flexi/fl-flexi-test.py \
    ~/flexi-scratch/effects/com.example.cpp_invert.v1 --image frame.png
```

The harness needs a Python with NumPy, such as a Flexi platform's; the effect itself does not.
