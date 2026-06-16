# Render Preset Reader

Load render presets saved in user preferences

Render settings saved in preferences can be loaded ane re-applied through API calls or saved to JSON for later use.
This script can either be run from the command-line or loaded as a module by another Python script.
This lets you use Baselight or Daylight as a GUI for configuring render settings.
 
## Command Line

Run with no commands to dump render settings saved in the current user preferences file to *render_deliverables.json*

```
render_preset_reader.py
```

You can also specify the path to a Baselight preferences file to load settings from:

```
render_preset_reader.py /usr/fl/etc/blsiteprefs
```

## Python Module

Call from another Python script with:

```
    import render_preset_reader
    render_presets = RenderPresetReader.auto().read()
```

Or with a specific path:

```
    import render_preset_reader
    render_presets = RenderPresetReader(Path('path/to/bluserprefs'))
    render_presets.read()
```

Read from a stored JSON file with:

```
    render_presets = RenderPresetReader.from_json('path/to/myfile.json')
```

Once presets are read, here are example uses to save values or apply them for a render:
  
```
    deliverables = render_presets.deliverables                      # list of flapi.RenderDeliverable objects
    dicts = render_presets.to_dicts()                               # (optional) list of plain dicts
    specific_deliverable = render_presets.get('deliverable_name')   # retrieve a specifc RenderDeliverable by name

    for d in render_presets.deliverables:
        print(d.Name)
    render_presets.to_json('path/to/myflie.json')                   # dump to JSON file
    renderSetup.add_deliverable(render_presets.get('My Named Deliverable')) # use a named preset for a render 
```