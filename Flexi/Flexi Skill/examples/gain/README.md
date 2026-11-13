# Example Gain

The smallest complete Flexi effect: one image in, one image out, one slider.

Start a new effect from this folder. It shows the parts every Python effect needs:

- `flexi_gain.py` subclasses `flexi.Effect` and implements `describe_effect`,
  `query_vram_requirement`, `set_vram_limit` and `run_generate`.
- `com.example.gain.v1.flexi` declares the effect and how to install it on Apple silicon,
  Intel Macs (`macos-intel`, PyTorch 2.2) and Linux.
- `flexi.py` is not here: copy it from an installed effect on your system.

Images arrive as shared memory on macOS and CUDA buffers on Linux; the `open_input`,
`open_output` and `write_output` helpers hide the difference.
