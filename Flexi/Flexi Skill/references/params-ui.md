# Params and UI

Params go in the `params` list of the `describe_effect` reply; their values arrive in
`data['params']` by name, evaluated at the frame being rendered. The schema is
`flexi_reply_v1.schema`.

```python
'params': [
    {'name': 'strength', 'label': 'Strength', 'type': 'float',
     'default': 1.0, 'range': [0.0, 2.0, 0.01], 'animated': True,
     'tooltip': 'How strongly the effect is applied.', 'uilocation': [0, 0]},

    {'name': 'mode', 'label': 'Mode', 'type': 'enum', 'default': 0, 'ui': 'radio',
     'values': [{'value': 0, 'label': 'Fast'}, {'value': 1, 'label': 'Quality'}],
     'uilocation': [0, 1]},

    {'name': 'detail', 'label': 'Detail', 'type': 'float',
     'default': 0.5, 'range': [0.0, 1.0], 'uilocation': [0, 2],
     'visible_if': [{'mode': [1]}]},

    {'name': 'invert', 'label': 'Invert', 'type': 'bool', 'default': 0, 'uilocation': [0, 3]},

    {'name': 'label', 'label': 'Label', 'type': 'string', 'default': '',
     'empty_message': 'Enter a label', 'uilocation': [0, 4]},
]
```

| Field | Notes |
|---|---|
| `type` | `float`, `int`, `enum`, `bool` (sent as 0/1), `string`; positions: see below |
| `range` | `[min, max]` or `[min, max, step]`, never separate `min`/`max` keys |
| `animated` | `False` stops keyframing (floats, points, rects). Ints are never animated. |
| `values` | Enums: a list of `{value, label}` |
| `ui` | `'noslider'` (int, float, point or rect without sliders), `'radio'` (enum as buttons; otherwise a list), `'sliders'` (lists: full controls per item) |
| `tooltip` | Hover text |
| `uilocation` | `[page, row]` or `[page, row, column]`. Required: a param without one stops the effect's UI from building. |
| `visible_if` | Tests on other enum or bool params: visible if any test passes; within a test every key must match one of its values |
| `visibility_rules` | Visible and enabled states by condition, see below |
| `empty_message` | Strings: shown while the value is empty |

`visible_if` examples:

```python
[{'mode': [1, 2]}]                              # mode is 1 or 2
[{'mode': [1], 'level': [2]}]                   # mode is 1 and level is 2
[{'mode': [1]}, {'mode': [3], 'level': [2]}]    # either test
```

`visibility_rules` alternates a test (as in `visible_if`) and the state it sets; later matching
rules win. The state before any rule is the opposite of what the first rule sets, so one rule is
enough for "only when":

```python
'visibility_rules': [{'mode': [1]}, {'visible': 1},
                     {'mode': [1], 'invert': [1]}, {'enabled': 0}]
```

Two params can share a `uilocation` when their visibility never overlaps.

Several pages: list the names in `uipages` (required for more than one page) and put the page
index first in each `uilocation`.

Scenes store the param list. Adding, removing, renaming, retyping or reordering a param, or
changing a list's attributes, needs a new effect `version`; see `references/manifest.md`.
Labels, ranges, defaults and layout are read from the installed effect and can change freely.

## Points, rects and lists

Positions the user places in the viewer. Put them after every float, int, enum, bool and string
param: a simple param after one of these stops the effect's UI from building.

```python
{'name': 'centre', 'label': 'Centre', 'type': 'point', 'default': [0.5, 0.5],
 'drawstyle': {'shape': 'Diamond', 'colour': [1.0, 0.5, 0.0], 'label': 'Centre'},
 'uilocation': [0, 6]},

{'name': 'box', 'label': 'Box', 'type': 'rect', 'default': [0.25, 0.25, 0.75, 0.75],
 'uilocation': [0, 7]},
```

- `default` is required: `[x, y]` or `[x_min, y_min, x_max, y_max]` as fractions of the frame
  width and height, from the top left.
- In `run_generate` a point arrives as `{'X': ..., 'Y': ...}` and a rect as
  `{'XMin', 'YMin', 'XMax', 'YMax'}`, in frame pixels at full resolution, at the frame being
  rendered. Map them into buffers as in `references/geometry.md`.
- `fl-flexi-test` (and so fl-diag) in 7.0.3 sends them as the `default` list instead, and lists
  as `[]`. Accept both forms:

```python
def point_px(value, data):
    if isinstance(value, dict):
        return value['X'], value['Y']
    return value[0] * data['width'], value[1] * data['height']   # fl-flexi-test
```

**Lists**: `point_list` and `rect_list` hold any number of items the user adds, each with its
own `attributes` (`bool`, `enum` or `string`, with `default`, `label`, optional `animated`,
`modifier: 'Shift'` for a bool that items added with Shift held start with the opposite of its
`default`, `uiwidth` for a string; `{unique_id}` in a
string default numbers the items). Items arrive as a list of dicts: the coordinates plus each
attribute, bools as 0/1.

```python
{'name': 'points', 'label': 'Points', 'type': 'point_list',
 'attributes': [{'name': 'Enabled', 'type': 'bool', 'default': True, 'animated': True},
                {'name': 'Negative', 'type': 'bool', 'modifier': 'Shift'},
                {'name': 'name', 'label': 'Name:', 'type': 'string', 'uiwidth': 18,
                 'default': 'Point {unique_id}'}],
 'drawstyle': {'label': '{name}'},
 'drawstyle_rules': [{'Negative': True}, {'colour': [0.6, 0.0, 0.0], 'shape': 'Diamond'}],
 'uilocation': [0, 8]}
```

`drawstyle` sets `label` (`{attribute}` is replaced), `colour`, `shape`, `font_size`, `faint`;
`drawstyle_rules` alternates a test on attributes and the style it applies. `rect_list` also takes
`onlyone: True`.

**Objects**: an `object_list` groups one `point_list` and one `rect_list` per object, as in
point-and-box segmentation. Name both in `contained_params` and define them (without their own
`uilocation`) before it; `ui_selector_attribute` names one of its string attributes, shown to pick
an object:

```python
{'name': 'objects', 'label': 'Objects', 'type': 'object_list',
 'attributes': [{'name': 'objName', 'label': 'Name:', 'type': 'string', 'uiwidth': 120,
                 'default': 'Object {unique_id}'}],
 'contained_params': ['rects', 'points'], 'ui_selector_attribute': 'objName',
 'uiheight': 5, 'uilocation': [0, 3]}
```

Each object arrives as its attributes plus `ObjectID` and the two lists by name:
`data['params']['objects'][0]['points'][0]['X']`.

## Colour space

Models expect a particular encoding, usually display sRGB. Let Baselight convert the inputs
rather than converting in the effect.

Fixed, in the describe reply:

```python
'input_colour_space':  'sRGB_Display',
'output_colour_space': 'sRGB_Display',
```

Both must name a colour space: the file names, without `.flspace`, in
`<app>/etc/colourspaces/` (`sRGB_Display`, `Rec709_lin`, `ACEScct`,
`FilmLight_TLog_EGamut2`, …), or a colour space in the scene. Any other name, `'Input'` and
`'Auto'` included, stops users from adding the effect ("specifies an unknown input colour
space"). `output_colour_space` names the space the effect writes; without it, the output is in
the input's colour space. Alpha is not converted.

Chosen by the user: add an enum param named `_colourspace_<input name>`. It overrides
`input_colour_space` for that input and also accepts `'Input'` (the colour space of the stack at
that point) and `'Auto'` (the working colour space). Leave the labels empty; Baselight fills in
the real names. It is read once, not per frame: do not animate it.

```python
{'name': '_colourspace_src', 'label': 'Colour Space', 'type': 'enum',
 'default': 'sRGB_Display', 'uilocation': [0, 5],
 'values': [{'value': 'sRGB_Display', 'label': ''},
            {'value': 'Input', 'label': ''},
            {'value': 'Auto', 'label': ''}]}
```

A display-referred model given scene-linear or log data gives wrong results without any error,
so test with real graded footage as well as sRGB stills.
