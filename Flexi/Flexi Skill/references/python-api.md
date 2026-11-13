# Python API (`flexi.py`)

Subclass `flexi.Effect`, register the `(identifier, version)` pairs this process serves, and
hand control to `flexi.run()`:

```python
if __name__ == '__main__':
    effect = MyEffect()
    effect.init([('com.yourstudio.my_effect', 1)])
    flexi.run()
```

## Threads

`run_generate`, `set_vram_limit` and `test_effect` run one at a time on a single worker thread.
`describe_effect` and the `query_*` methods run on the event-loop thread, possibly while a
`run_generate` is in progress, so they must be quick and must not touch the model or the GPU.

## Methods

| Method | Required | Returns |
|---|---|---|
| `describe_effect(self, effect_id)` | Yes | Description dict, or `flexi.error(message, detail)` |
| `query_vram_requirement(self, effect_id, data)` | Yes, unless in `local_methods` | `{'min_mb': int, 'max_mb': int}` |
| `set_vram_limit(self, effect_id, data)` | Yes | `{}` once usage ≤ `data['limit_mb']`, or `'quit'` |
| `run_generate(self, effect_id, instance, data)` | Yes | `{}`, or `{'metadata': {...}}` |
| `query_input_rects(self, effect_id, data)` | If listed in `supported_methods` | `{'inputs': {'<name>': {'rect': {...}}}}` |
| `query_output_rect(self, effect_id, data)` | If listed in `supported_methods` | `{'output': {'rect': {...}}}` |
| `test_effect(self, effect_id, data)` | Optional | `{'ok': True/False, 'message': str}` |
| `setup_if_necessary(self, effect_id, gpu)` | Do not use | `flexi.py` also calls it straight after `describe_effect`, before any VRAM grant; load models in `run_generate` instead |
| `shutdown(self)` | Optional | Clean-up before exit |

`effect_id` is `(identifier, version)`; `instance` names the operator instance in the scene.
`data` is described in `flexi_message_v1.schema`.

Errors and warnings go in the reply:

```python
return flexi.error('Model file missing', path)              # fails the call, shown to the user
return {'__LOG__': [{'level': 4, 'message': 'Low light', 'detail': ''}]}   # a warning
```

An exception in a method becomes an "Internal error" reply. `flexi.py` sends Baselight only the
exception and prints the traceback to the effect's output (see Logging in
`references/protocol.md`). Keep stdout quiet otherwise.

## The describe reply

```python
return {
    'process_mode': {'linux': 'cuda_ipc', 'macos': 'shm'},
    'inputs':  [{'name': 'src', 'label': 'Source', 'type': 'image', 'format': '3XFLOAT', 'planar': True}],
    'outputs': [{'name': 'out', 'label': 'Result', 'type': 'image', 'format': '3XFLOAT', 'planar': True}],
    'params':  [...],                      # references/params-ui.md
    'help':    'What the effect does and how to use it.',
}
```

**Inputs**: `name` (a C identifier), `label`, `type` (`'image'`), `format` (`3XFLOAT`, `1XFLOAT`
for a matte, `4XFLOAT`), `planar`, `optional`, `is_matte`, `temporal` (frame offsets, see
`references/temporal.md`), `normalise` (`{'mean': [...], 'std': [...]}`, applied by Baselight
before the data reaches you).

**Outputs**: one entry with `name`, `label`, `type`, `format`, `planar`, and optionally
`denormalise`. `'outputs': None` for an effect without an image output. In a `4XFLOAT` output the
fourth channel is the image's alpha, which Baselight uses as opacity: carry it through from the
input, and never put other data in it.

Always give `format`: Baselight rejects an input without one and silently drops an output
without one.

Other keys:

| Key | Use |
|---|---|
| `fixed_image_size` | `{'width', 'height', 'scaling': 'fit_inside'/'fill', 'position': 'centre'/'top_left', 'pad_value'}`: the effect always sees this size; Baselight scales in and out |
| `input_colour_space`, `output_colour_space` | Fixed colour spaces, see `references/params-ui.md` |
| `local_methods` | Answers Baselight computes itself, see `references/protocol.md` |
| `roi_sensitive` | `True` when the output changes with the area rendered (whole-frame models) |
| `uipages` | Page (tab) names |
| `help` | Help text; `*bold*` and backtick code are formatted |

## `run_generate` data

`data` holds `params` (values at this frame, by name), `inputs` (keyed `'<name>:<offset>'`, e.g.
`'src:0'`), `output`, `width`, `height`, `inputs_hash` and `metadata`. Each input and the
output has a `rect` (`left`, `top`, `width`, `height`): the buffer covers that area only, which
can be smaller or larger than the frame and can differ between input and output.

- `inputs_hash` is the same when the inputs are the same: use it to skip repeated work while a
  colourist adjusts params on one frame.
- Metadata: each input entry's `metadata` holds that image's string metadata, and
  `data['metadata']` the render's. Return `{'metadata': {...}}` to add or replace keys on the
  output.

## I/O helpers

They detect shared memory or CUDA IPC from the message, so one code path serves both. The arrays
are float32 numpy (shm) or numba CUDA arrays (cuda_ipc); `torch.as_tensor` accepts both.

```python
def run_generate(self, effect_id, instance, data):
    import torch
    if self.model is None:
        self.device = self.get_torch_device()
        self.model = self.load_model()

    with self.open_input(data['inputs'], 'src', channels=3, planar=True) as (src, irect), \
         self.open_output(data['output'], channels=3, planar=True) as (out, orect):
        image = torch.as_tensor(src).to(self.device).unsqueeze(0)
        with torch.inference_mode():
            result = self.model(image)[0]          # (3, H, W): no batch axis
        self.write_output(out, orect, result, irect)
    return {}
```

- `get_torch_device()` picks CUDA, MPS or CPU, enables TF32, makes cuDNN deterministic and turns
  off autograd for the calling thread. Call it inside `run_generate` and always assign its result:
  `self.device = self.get_torch_device()`. `write_output` uses `self.device`, and
  `get_torch_device()` does not set it, so a bare call leaves the effect silently running on the
  CPU.
- `open_input(inputs, name, channels, planar=False, temporal_index=0)` and
  `open_output(output, channels, planar=False)` yield `(array, rect)`. A 1-channel buffer is
  `(1, H, W)` when planar, `(H, W, 1)` otherwise.
- **Use the arrays only inside the `with` block.** Shared memory is unmapped when it ends: an
  array or CPU tensor that still points into it crashes the process. Copy what you need to keep.
- `write_output(out, out_rect, result, result_rect)` copies the overlap of the two rects, with
  the result's layout matching the output's (planar `(C, H, W)` or interleaved `(H, W, C)`).
- The helpers handle `shm` and `cuda_ipc`. In `file` mode the files are named in
  `data['inputs'][key]['file']` and `data['output']['file']`: pass them to a tool as
  `examples/run-tool` does, or read and write them yourself.

## Rect helpers

`union_rect`, `intersect_rect` (returns `'empty'` when they do not overlap), `extend_rect(rect,
x, y)`, `transform_point`, `transform_rect`, `invert_transform`. Use `extend_rect` in
`query_input_rects` when the model needs context around the output area (convolutions, tiling),
or the `local_methods` shortcut.

## Loading weights

```python
WEIGHTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weights', 'model.pth')
state = torch.load(WEIGHTS, map_location='cpu', mmap=True, weights_only=True)
```

See `references/weights.md`.
