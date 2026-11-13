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
| `type` | `float`, `int`, `enum`, `bool` (sent as 0/1), `string` |
| `range` | `[min, max]` or `[min, max, step]`, never separate `min`/`max` keys |
| `animated` | Floats only. `False` stops keyframing. |
| `values` | Enums: a list of `{value, label}` |
| `ui` | `'noslider'` (int/float without a slider), `'radio'` (enum as buttons); an enum is otherwise a list |
| `tooltip` | Hover text |
| `uilocation` | `[page, row]` or `[page, row, column]`. Required: a param without one stops the effect's UI from building. |
| `visible_if` | Tests on other int, enum or bool params: visible if any test passes; within a test every key must match one of its values |
| `empty_message` | Strings: shown while the value is empty |

`visible_if` examples:

```python
[{'mode': [1, 2]}]                              # mode is 1 or 2
[{'mode': [1], 'level': [2]}]                   # mode is 1 and level is 2
[{'mode': [1]}, {'mode': [3], 'level': [2]}]    # either test
```

Several pages: list the names in `uipages` (required for more than one page) and put the page
index first in each `uilocation`.

Scenes store the param list. Adding, removing, renaming or retyping a param needs a new effect
`version`; see `references/manifest.md`.

## Colour space

Models expect a particular encoding, usually display sRGB. Let Baselight convert in and out
rather than converting in the effect.

Fixed:

```python
'input_colour_space':  'sRGB_Display',
'output_colour_space': 'sRGB_Display',
```

For `input_colour_space`, `'Input'` (the colour space of the stack at that point) and `'Auto'`
(the working colour space) are also accepted. `output_colour_space` must name a colour space;
without one, the output is tagged with the input's colour space.

Chosen by the user: add an enum param named `_colourspace_<input name>`. Leave the labels empty;
Baselight fills in the real names.

```python
{'name': '_colourspace_src', 'label': 'Colour Space', 'type': 'enum',
 'default': 'sRGB_Display', 'uilocation': [0, 5],
 'values': [{'value': 'sRGB_Display', 'label': ''},
            {'value': 'Input', 'label': ''},
            {'value': 'Auto', 'label': ''}]}
```

A display-referred model given scene-linear or log data gives wrong results without any error,
so test with real graded footage as well as sRGB stills.
