# The `.flexi` manifest

JSON that must validate against `flexi_effects_definition_v1.schema` (in the Baselight
install's `etc/`). One file can declare several effects, such as variants or versions, served
by one process or by different launch commands. Name the file `<identifier>.v<version>.flexi`.

```json
{
    "flexi_effects_definition_v1": {
        "effects": [
            {
                "identifier": "com.yourstudio.my_effect",
                "version": 1,
                "label": "My Effect",
                "short_label": "My Effect",
                "description": "What the effect does, in one sentence.",
                "licence": "LICENCE.md",
                "type": "filter",
                "launch_command": "./bin/python3 flexi_my_effect.py"
            }
        ],
        "install": {
            "all": {
                "python-packages": ["timm==1.0.15"],
                "sources": {
                    "flexi.py": "flexi.py",
                    "flexi_my_effect.py": "flexi_my_effect.py",
                    "my_model": "my_model",
                    "LICENCE.md": "LICENCE.md"
                },
                "weights": {
                    "weights/my_model.pth": "weights/my_model.pth"
                }
            },
            "linux": { "flexi_platform": "pytorch-2.8" },
            "macos": { "flexi_platform": "pytorch-2.8" },
            "macos-intel": { "flexi_platform": "pytorch-2.2" }
        }
    }
}
```

## Effect fields

| Field | Notes |
|---|---|
| `identifier` | Your reverse-domain name, stable across releases. Never `uk.ltd.filmlight.*`. |
| `version` | Integer. Scenes store each effect's description: bump the version whenever params are added, removed, renamed, retyped or reordered, or a list's attributes change, and keep the old version installed so existing scenes still render. |
| `label`, `short_label` | Shown in the UI |
| `description` | Required |
| `licence` | Required. A file in the effect folder (`LICENCE.md`), or the text itself. A single word with no space is always read as a file name, so write `"MIT licence"`, not `"MIT"`. Include the model's upstream licence. |
| `type` | `filter` (image in, image out: the layer operator), `source` (no input: a Flexi Source), `multi_input` (several inputs: the Flexi Effect strip only). `metadata` and `internal` effects are hidden from the menus, so third-party effects use `filter`, `source` or `multi_input`. |
| `launch_command` | Run in the installed effect folder. `./bin/python3` is the effect's own venv on its platform. Environment variables may prefix it: `PYTORCH_ENABLE_MPS_FALLBACK=1 ./bin/python3 …`. On macOS the folder path contains a space, so quote any path you build from `$PWD`. |
| `supported_methods` | Optional methods the effect implements: `query_input_rects_v1`, `query_output_rect_v1`, `test_effect_v1`. Without them the rect queries are never sent. |
| `output_type` | Leave it out. Only `depth` and `trimap` mean anything, and both are for FilmLight's own effects. |

## Install fields

`install` has an `all` section and per-platform sections. The installer uses `macos-intel`
instead of `macos` on Intel Macs (it replaces `macos` entirely, it is not merged), and `macos`
on Apple silicon.

| Field | Notes |
|---|---|
| `flexi_platform` | The shared Python + PyTorch runtime the effect's venv is built on: `pytorch-2.8` on Linux and Apple silicon, `pytorch-2.2` on Intel Macs (PyTorch has no newer Intel Mac builds). Installed once with Baselight's Flexi effects and shared by every effect. List them in `<flexi dir>/platforms/`. |
| `python-packages` | Extra packages for the effect's venv. Pin every one (`"timm==1.0.15"`). Never list `torch`, `torchvision`, `numpy` or anything else the platform provides. A package that must differ by OS goes in that OS's section. `pip` also looks for wheels next to the `.flexi` file, so a private wheel can ship beside it. |
| `sources` | Files and folders copied into the effect. A list of paths, or an object mapping **destination path in the installed effect → source path next to the `.flexi`** (the schema's own description has this backwards). Always include `flexi.py` for Python effects. The installer cannot fetch `https://` sources: ship the files. |
| `weights` | Same format as `sources`, kept separate so packages can carry or omit them. See `references/weights.md`. |
| `python-version` | Ignored when a `flexi_platform` is given: the platform's Python is used |
| `run` | Extra install commands, run in the effect folder |
| `download` | `{"web_page": …, "web_instructions": …}`, shown when a scene uses the effect on a machine where it is not installed |

Tar archives (`.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.txz`) listed in `sources` or
`weights` are unpacked into the effect folder. Prefix the source with `-` to copy one as it is.

## Validate

```bash
<python with jsonschema> <app>/share/flexi/flexi_validate.py \
    <app>/etc/flexi_effects_definition_v1.schema com.yourstudio.my_effect.v1.flexi
```

On macOS `share` and `etc` are under `<app>/Contents/`. The Flexi platform's Python has
`jsonschema`: `<flexi dir>/platforms/<platform>/bin/python3` (`pytorch-2.8`, or `pytorch-2.2` on an
Intel Mac).
