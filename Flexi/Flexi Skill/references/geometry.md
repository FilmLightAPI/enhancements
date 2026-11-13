# Rects, fixed size and coordinates

How Baselight decides which pixels an effect sees, and how to map positions between the frame,
the buffers and a model's fixed input size.

## Coordinates

Everything is in **working-format pixels at full resolution**: origin at the top left, Y down,
pixel edges on integers. Input and output `rect`s, point and rect params, and the
`working_rect` sent with rect queries all use this space, whatever the proxy or viewer zoom.

A buffer covers only its `rect`. To find a frame position in a buffer, subtract the buffer's
`left` and `top`:

```python
with self.open_output(data['output'], channels=3, planar=True) as (out, orect):
    p = data['params']['centre']     # {'X': ..., 'Y': ...}; fl-flexi-test: see params-ui.md
    col = int(p['X']) - orect['left']
    row = int(p['Y']) - orect['top']
    if 0 <= col < orect['width'] and 0 <= row < orect['height']:
        out[:, row, col] = 1.0
```

A rect can also be the string `"empty"` (nothing to render: return `{}`) or `"infinite"`.

## Which area the effect gets

**Without rect methods** (neither `query_*_rect*` in `supported_methods` nor `local_methods`):

- The output rect is the area Baselight needs, clipped to the working format. It is the whole
  frame only when the whole frame is rendered.
- Every input buffer covers the same rect as the output. Where the input has no image, the
  buffer holds the input's outside colour.
- So an effect that looks at neighbouring pixels (blur, convolution) has nothing beyond the
  buffer's edge, and is wrong along the edges of every partial render (a zoomed viewer, a
  tile): declare the margin it needs, below.

**With rect methods**:

- `query_input_rects` receives the output rect wanted (`data['output']['rect']`) and
  `data['working_rect']` (always the whole working format). It replies with the area each input
  needs, keyed by input name without the `:offset`. One rect covers every temporal frame of that
  input; an input left out gets the working format.
- `query_output_rect` receives the input rects and replies with the area the effect can produce;
  Baselight clips it to the area requested. Without this method the output cannot extend past
  the working format.
- Each input buffer is then exactly the input's image within the rect asked for, with no
  padding: index by the rect you are given, which can be smaller than asked at the frame edges.

The `local_methods` shortcut answers both inside Baselight (see `references/protocol.md`).
For `query_input_rects_v1`, an input's entry can be:

| Entry | Input rect |
|---|---|
| `'output'` | The output rect |
| `['output', 16]` | The output rect grown by 16 pixels on every side |
| `['output', 'radius']` | Grown by the `radius` param, rounded up |
| `{'rect': {'left': 0, 'top': 0, 'width': 512, 'height': 512}}` | Always this rect |

**Outside the output rect**, Baselight extends a 1-channel output by repeating its edge pixels,
and gives an RGB(A) output the outside colour of the main input.

## `roi_sensitive`

`'roi_sensitive': True` in the describe reply makes Baselight render the effect over the whole
frame at full resolution, cache the result and reuse it for every view, zoom and proxy. Set it
for models whose output depends on the whole image (segmentation, depth, matting): without it,
a zoomed-in viewer renders only part of the frame and the model sees only that part.

## `fixed_image_size`

For a model that only works at one size, Baselight can do the resizing. In the describe reply:

```python
'fixed_image_size': {'width': 1024, 'height': 1024, 'scaling': 'fit_inside'},
'roi_sensitive': True,
```

| Field | Meaning |
|---|---|
| `width`, `height` | Required. The size every input and the output buffer will have. |
| `scaling` | `'fit_inside'` (default): scale uniformly to fit, pad the rest. `'fill'`: scale width and height separately to fill the size, stretching the image. |
| `position` | With `fit_inside`: `'centre'` (default) or `'top_left'` |
| `pad_value` | Colour of the padding: a number, or `[r, g, b, a]`. Default 0. A negative number uses the input's outside colour. |

Then:

- Every input and the output buffer have rect `{'left': 0, 'top': 0, 'width': W, 'height': H}`,
  and `data['width']`, `data['height']` are W and H.
- `query_input_rects` and `query_output_rect` are not called (nor their `local_methods`).
- Baselight resizes the output back onto the frame itself.
- The area fitted into W×H is the first area Baselight renders. Set `roi_sensitive: True` so that
  this is always the whole frame; otherwise the result depends on what the viewer showed first.

Example: a 1920×1080 frame into 1024×1024 with `fit_inside` and `centre` is scaled by 0.533;
the image fills rows 224 to 800 and rows above and below are padding.

## `transform_to_fixed`

In fixed-size mode `run_generate` data includes `transform_to_fixed`, which maps frame
coordinates to coordinates in the W×H buffers. Use it for point and rect params, which are in
frame coordinates:

```python
t = data['transform_to_fixed']        # {'Xx', 'Xy', 'X0', 'Yx', 'Yy', 'Y0'}
# x' = Xx*x + Xy*y + X0,   y' = Yx*x + Yy*y + Y0
p = dict(data['params']['centre'])
self.transform_point(p, t)            # changes p in place, returns None
```

`flexi.py` has:

- `transform_point(point, t)`: maps `point['X']`, `point['Y']` in place.
- `transform_rect(rect, t)`: maps `XMin`, `YMin`, `XMax`, `YMax` in place (the two corners only).
- `invert_transform(t)`: returns the reverse transform, from the W×H buffer back to the frame,
  for positions the model finds (detections, keypoints) that you report or draw.

Copy a param before transforming it if you need the original. It is the only transform Baselight
sends: outside fixed-size mode, positions and rects are already in the same frame coordinates.

## Thumbnails

Baselight does not run effects for thumbnails. A thumbnail shows the effect's main input, its
green channel for a matte output, or black for a `source` effect.
