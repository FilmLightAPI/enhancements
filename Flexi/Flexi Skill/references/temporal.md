# Temporal effects

An effect can ask for frames around the current one by declaring offsets on an input:

```python
'inputs': [{'name': 'src', 'label': 'Source', 'type': 'image', 'format': '3XFLOAT',
            'planar': True, 'temporal': [-1, 0, 1]}]
```

`run_generate` then receives `data['inputs']['src:-1']`, `['src:0']` and `['src:1']`.

## How temporal rendering works

- **One call per output frame.** Baselight calls `run_generate` once for each frame it renders,
  each time with that frame's window of inputs.
- **Relative offsets only.** There is no absolute frame number or timecode in the message.
- **Frames outside the shot are missing.** At the start and end of a shot the key for an
  out-of-range offset is absent or `None`. Check before opening it:

  ```python
  present = [t for t in (-1, 0, 1) if data['inputs'].get(f'src:{t}')]
  ```

- **No guaranteed order.** Frames are rendered in whatever order the user or the render queue
  asks for: forwards, backwards, one frame while grading, or spread across several GPUs and
  machines at once. Each process sees an arbitrary subset.
- **`inputs_hash` covers all the inputs**, so with a temporal window it changes every frame. It
  tells you the inputs are the same as last time (a colourist adjusting params on one frame), not
  which frame you are on.

## What follows

The output for a frame must depend only on that frame's inputs and params. Do not carry state
from one `run_generate` call to the next (running averages, trackers, previous outputs): the
result would change with render order and differ between the viewer and the render.

Use as few offsets as the effect needs. Each offset is another frame decoded and transferred for
every output frame, and a model that processes N frames jointly costs N times as much per output
frame.

`examples/temporal-average` shows a three-frame window, missing frames at shot edges, and RGBA
input and output with alpha carried through.
