# Flexi Skill

Teaches your coding agent to write, test and package Flexi effects for Baselight.

Flexi effects are programs, usually Python and PyTorch but any language, that Baselight launches
and drives to render frames. This skill gives a coding agent what it needs to write one from a
plain-English request: the protocol, the `flexi.Effect` Python API, the `.flexi` manifest,
params and UI, temporal inputs, model weights, VRAM, testing, and packaging for Linux, Apple
silicon and Intel Macs, with five working examples. It is written for the Flexi tools in
Baselight 7.0.3.

It uses the open [Agent Skills](https://agentskills.io) `SKILL.md` format, read by Claude Code,
Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode and other agents.

## What you need

- Baselight or Daylight 7.0.3 or later, with FilmLight's Flexi effects installed (they install
  the shared Python and PyTorch platforms that effects run on).
- To build Python effects: the Python 3.12 that Baselight uses (python.org's on macOS).
- A GPU Flexi supports: NVIDIA on Linux, Apple silicon or a Metal GPU on macOS, with at least
  16 GB of VRAM (24 GB of unified memory on Apple silicon).
- A coding agent.

## Install

Put this folder in your agent's skills folder, named `flexi`. For Claude Code, either unzip the
download into `~/.claude/skills/flexi`, or clone this repository and link the folder:

```bash
git clone https://github.com/FilmLightAPI/enhancements.git ~/fl-enhancements
mkdir -p ~/.claude/skills
ln -s "$HOME/fl-enhancements/Flexi/Flexi Skill" ~/.claude/skills/flexi
```

Other agents have their own skills folder (often `~/.agents/skills/`): see their documentation.
If your agent does not support skills, keep this folder where it can read it and ask it to read
`SKILL.md` before it starts.

## Using it

Open your agent in a new folder on a machine with Baselight and ask in plain English:

> Turn this PyTorch denoiser into a Flexi effect for Baselight, with a strength slider, and test it.

> Package my effect for Linux and macOS, with its weights.

The agent reads the protocol and schemas from your Baselight install, copies `flexi.py` from
FilmLight's installed Flexi effects, starts from the closest example, and tests with
`fl-install-flexi-effect` and `fl-flexi-test`. `flexi.py` is FilmLight's module and is not
included here.

## Examples

| Example | Shows |
|---|---|
| `examples/gain` | The minimal effect |
| `examples/temporal-average` | Temporal inputs and RGBA images |
| `examples/person-matte` | Model weights, normalised input, matte output, VRAM that adapts to the grant |
| `examples/run-tool` | Wrapping an existing command-line tool, with images as files |
| `examples/cpp-invert` | A compiled C++ effect using shared memory; native binaries and signing |

## Distributing your effects

Packages you build with `fl-make-flexi-package` contain your effect only and are **not signed or
notarized by FilmLight**. On macOS, sign them with your own Developer ID and notarize them with
your own Apple account, or have your users install them from the command line. Build one package
per platform (Linux, Apple silicon, Intel Mac), on that platform. See
`references/distribution.md` for what each machine needs.

## Tested with

With Baselight 7.0.3 on Apple silicon and on an Intel Mac, every example installs with
`fl-install-flexi-effect` and produces the output it should, and all but `run-tool` pass
`fl-flexi-test` (its 7.0.3 version does not drive `file`-mode effects). On Linux with an NVIDIA
GPU, every example produces the output it should under a test harness.

Claude Code with this skill wrote a working effect from a plain-English request (an invert, a
blur, a temporal difference, and an effect with model weights) in 12 tries out of 12, each
installed with Baselight 7.0.3's tools and checked. Other agents read the same `SKILL.md` but
have not been tried yet.
