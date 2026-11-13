---
name: flexi
description: Write, test, package and distribute Flexi effects for FilmLight Baselight and Daylight — programs (usually Python + PyTorch, but any language) that Baselight launches and drives over a websocket to render frames. Use when turning a machine-learning model or image-processing code into a Baselight effect; writing a .flexi manifest; implementing flexi.Effect methods (describe_effect, run_generate, query_vram_requirement, set_vram_limit); defining params and UI; handling temporal inputs, model weights or VRAM; debugging an effect that will not load or render; testing with fl-flexi-test; or packaging and installing with fl-install-flexi-effect, fl-make-flexi-package and fl-flexi, on Linux, Apple silicon or Intel Macs.
---

# Flexi effects for Baselight

A Flexi effect is a separate program. Baselight starts it, connects over a websocket, and sends
JSON-RPC messages: describe yourself, how much VRAM do you need, render this frame. Images arrive
as shared memory (macOS), CUDA buffers (Linux) or image files. Most effects are Python, using the
`flexi.py` module that ships with Baselight, but any language works.

## Before writing code

1. **Find the user's install and read it.** It matches the build the effect will run on:

   | What | Where (`<app>` = Baselight .app or install; add `Contents/` on macOS) |
   |---|---|
   | Protocol overview | `<app>/doc/FlexiEffects.md` |
   | Schemas: manifest, messages, replies | `<app>/etc/flexi_*_v1.schema` |
   | Test harness, schema validator | `<app>/share/flexi/fl-flexi-test.py`, `flexi_validate.py` |
   | Tools | `<app>/bin/fl-install-flexi-effect`, `fl-make-flexi-package`, `fl-flexi` (list, `check [--full]`, `remove`, `scene`; `-h` for usage) |
   | Flexi directory | `/vol/.support/flexi` (on macOS a link to `/Library/Application Support/FilmLight/flexi`) |
   | `flexi.py` | in any installed effect: `<flexi dir>/effects/*/flexi.py` |
   | Platforms (Python + PyTorch) | `<flexi dir>/platforms/` |

   If this skill and the install disagree, the install wins, with one exception: the manifest
   schema describes `sources` and `weights` objects backwards (see `references/manifest.md`).
2. **Run the model on its own first**: one image in, one out, on the target device.
3. **Start from the closest example** in `examples/`.

`flexi.py` is FilmLight's file: copy it from the user's install into the effect folder. Never
write a replacement or publish it.

## Examples

| Folder | Shows |
|---|---|
| `examples/gain` | The minimal effect. Start here. |
| `examples/temporal-average` | Temporal inputs `[-1, 0, 1]`, missing frames at shot edges, RGBA with alpha carried through |
| `examples/person-matte` | Model weights (downloaded, packaged, mmapped), normalised inputs, a matte output, VRAM measured and adapted to the grant |
| `examples/point-matte` | A point param placed in the viewer, `fixed_image_size`, `transform_to_fixed`, `roi_sensitive` |
| `examples/run-tool` | Wraps an existing command-line tool: images as files, a time limit, the tool's errors shown to the user |
| `examples/cpp-invert` | A compiled C++ effect: the protocol by hand, shared memory, a universal macOS binary |

## References

Read the one you need:

- `references/protocol.md`: launch, methods, caching, logs, timeouts
- `references/python-api.md`: `flexi.Effect`, the describe reply, I/O helpers
- `references/params-ui.md`: params, pages, visibility, points and rects, colour spaces
- `references/geometry.md`: rects, coordinates, `fixed_image_size`, `transform_to_fixed`, `roi_sensitive`
- `references/manifest.md`: the `.flexi` file and its install section
- `references/temporal.md`: frames around the current one
- `references/vram.md`: declaring, measuring, adapting, releasing
- `references/weights.md`: shipping model weights
- `references/testing.md`: scratch installs, `fl-flexi-test`, checking output
- `references/distribution.md`: packages per platform, native binaries, signing and notarization, what users need
- `references/other-languages.md`: the protocol without `flexi.py`, file mode, shared memory

## Rules that break effects when ignored

- **No GPU before the grant.** Nothing touches the GPU at import, in `__init__`,
  `describe_effect` or the `query_*` methods. Load the model in the first `run_generate`.
- **Query methods answer at once** and give the same reply to the same message: Baselight caches
  them. No model loading, no network, no `torch.cuda` calls.
- **`query_vram_requirement` returns `min_mb` and `max_mb`, measured**, covering everything the
  process allocates on the GPU (on CUDA, the context too).
- **`set_vram_limit` frees memory before replying**, or returns `'quit'`. On CUDA, answer 0 with
  `'quit'`.
- **Give every input and output a `format`** (`3XFLOAT`, `1XFLOAT`, `4XFLOAT`): Baselight
  rejects an input without one and treats an output without one as no output.
- **Pass `write_output` a 3-D result**: `(C, H, W)` planar or `(H, W, C)`. Drop the batch axis.
- **Deterministic output**, the same for a frame however and in whatever order it is rendered. No
  state carried between `run_generate` calls.
- **Bump `version` when params change**: scenes store the description.
- **Weights ship with the effect.** Never download at run time.
- **Pin every package**, and never list `torch` or `numpy`: the platform provides them.
- **Use your own identifier** (`com.yourstudio.name`), never `uk.ltd.filmlight.*`.
- **Keep stdout quiet**; report problems in the reply's `log`.

## Diagnosing

| Symptom | First check |
|---|---|
| fl-diag shows the effect as FAIL | Run the same checks yourself: `references/testing.md`, step 8. In 7.0.3 `file`-mode effects always fail its full test |
| Effect not in Baselight's menus | `fl-flexi check <id>`; schema errors; a required field missing (`identifier`, `version`, `label`, `description`, `type`, `licence`, `launch_command`); `type` must be `filter`, `source` or `multi_input`; Baselight restarted? |
| Fails to start | Run the `launch_command` by hand in the installed folder to see import errors; then `fl-flexi-test` |
| "Input format not defined" | Add `format` to the input |
| "specifies an unknown input colour space" | `input_colour_space` must be a file name from `<app>/etc/colourspaces/`; `'Input'` and `'Auto'` only work in a `_colourspace_` param |
| UI does not build | A param without `uilocation`; a simple param after a point, rect or list param |
| Black output, or no output | Output `format` missing; planar/interleaved mismatch; wrong channel count in `open_output`; 4-D result to `write_output` |
| Output shifted or cropped | Ignoring the `rect` of inputs and output; points used without subtracting the buffer's `left`/`top` (`references/geometry.md`) |
| Baselight hangs on the effect | A reply that is not a JSON object with the message's integer `id` |
| VRAM warnings, other effects failing | `min_mb`/`max_mb` too low, or `set_vram_limit` not freeing |
| A change to a query method has no effect | Cached reply: restart the effect (or Baselight) |
| Scene shows an error after params changed | Bump `version`, keep the old one installed |
| Different results on each render | See determinism in `references/testing.md` |
| Where are the effect's messages? | In the output of the Baselight process that launched it, prefixed with the identifier |
