# Testing

Test in this order. Each step catches problems the next makes harder to see.

## 1. The model on its own

Before any Flexi code: a plain script, one image in, one image out, on the target device (CUDA
on Linux, MPS on a Mac). Check that the weights load, the output range and channel order are
right, and the result looks right.

## 2. Install into a scratch folder

Check the manifest first with the validator in the install (see `references/manifest.md`): it
catches mistakes before they turn into install failures.

From the folder with the `.flexi` file, with `PLATFORM` the one the manifest names for this
machine (`pytorch-2.8`, or `pytorch-2.2` on an Intel Mac):

```bash
# The installer reads platform definitions from ./platforms
mkdir -p platforms
cp "<flexi dir>/platforms/$PLATFORM/$PLATFORM.flexiplatform" platforms/
# Use the installed platform rather than building a multi-GB copy in the scratch folder
mkdir -p ~/flexi-scratch/platforms
ln -s "<flexi dir>/platforms/$PLATFORM" ~/flexi-scratch/platforms/$PLATFORM
fl-install-flexi-effect -t ~/flexi-scratch com.yourstudio.my_effect.v1.flexi
```

- Without the platform file the installer stops with `Invalid flexi_platform '…' - definition
  not found`. Without the link it downloads and builds the whole platform under the scratch
  folder.
- The target gets a folder named after the `.flexi` file,
  `effects/com.yourstudio.my_effect.v1/`: sources, weights, and a venv whose
  `bin/python3` the `launch_command` uses. The venv is tied to its location: install again
  rather than moving it.
- To reinstall, delete `~/flexi-scratch/effects/com.yourstudio.my_effect.v1` first. `-f`
  installs over the old folder without clearing it, which nests directory sources inside
  themselves and keeps old weights, and it carries on past failed install steps, so a broken
  install can look successful.
- Installing into the Flexi directory itself needs `sudo` on most systems.

## 3. Drive it with fl-flexi-test

`fl-flexi-test.py` (in `<app>/share/flexi/`, under `Contents/` on macOS) plays Baselight: it
launches the effect, sends every method, renders frames at several sizes, and checks timing, VRAM
release and determinism, and the replies against the schema when `FL_FLEXI_REPLY_SCHEMA` names
it. Run it with the effect's own Python:

```bash
E=~/flexi-scratch/effects/com.yourstudio.my_effect.v1
FL_FLEXI_REPLY_SCHEMA=<app>/etc/flexi_reply_v1.schema \
    $E/bin/python3 <app>/share/flexi/fl-flexi-test.py $E --image frame.png --sizes 1920x1080,3840x2160 --runs 3 \
    --no-display
```

Always pass `--image` or `--synthetic`: the default test image is not shipped.

| Option | Use |
|---|---|
| `--image PATH` / `--synthetic` | A real test frame, or random noise |
| `--sizes WxH,…` | Frame sizes; include the largest your users have |
| `--runs N` | Renders per size; the first is cold |
| `--effect ID` | One effect of a multi-effect manifest |
| `--gpu N`, `--list-gpus` | Choose a GPU |
| `--no-pass3` | Skip the multi-GPU pass |
| `--verbose` | Print every message |
| `--json-summary` | One line of JSON with peak VRAM, RSS and timings |

It runs up to three passes:

- **Pass 1:** describe, then at each size grant VRAM, render, query VRAM, measure RAM; a
  bit-identical determinism check; shutdown.
- **Pass 2:** restart, render again, then `set_vram_limit 0`: the effect must free its memory or
  exit.
- **Pass 3:** several GPUs at once, on multi-GPU machines.

Non-Python effects have no venv: run the harness with the platform's Python
(`<flexi dir>/platforms/<platform>/bin/python3`: `pytorch-2.8`, or `pytorch-2.2` on an Intel Mac). The harness drives `shm` and
`cuda_ipc` effects only: test `file`-mode effects in Baselight, and see step 8.

## 4. Check the output, not just the run

The harness checks that the effect runs, not that its output is right, and does not save what
the effect produced. Check the output in two places:

- **On its own:** call the effect's processing function from a small script on a known input and
  compare with what it should produce.
- **In Baselight:** put the effect on a shot, render a frame with and without it
  (`bl-render -render out/f.%.4F.tif -range 0-0 <host:job:scene>`), and compare the files.

## 5. Determinism

The same frame must render bit-identically every time, in one process and in a fresh one. Effects
with temporal inputs must give the same frame whatever order frames are rendered in. Usual
causes: non-deterministic CUDA kernels (`get_torch_device()` sets deterministic cuDNN),
`torch.backends.cudnn.benchmark`, unseeded randomness, and state carried between calls.

## 6. `test_effect`

Implement `test_effect` (and list `test_effect_v1` in `supported_methods`) to run the model on a
small reference input shipped with the effect and compare with the expected result.
`fl-flexi check --full` calls it, so users can check an installation themselves.

## 7. In Baselight

Install into the Flexi directory (`fl-install-flexi-effect -t <flexi dir> …`), restart Baselight,
and check that:

- the UI matches the params, including pages and conditional visibility
- the output lines up with the source, with no shift at the edges or on cropped and
  repositioned shots
- scrubbing and grading stay responsive
- a render matches the viewer
- the effect works with several shots, and beside other Flexi effects on the same GPU

The effect's output and `log` entries appear in the output of the Baselight process that started
it (launch Baselight from a terminal to see them, or look in the Baselight logs).

## 8. `fl-flexi check` and fl-diag

Once the effect is in the Flexi directory, Baselight's diagnostics test it along with FilmLight's
effects: fl-diag's "Flexi effects integrity" and "Flexi effects full test" run on every installed
effect, and the site's diag report shows yours as FAIL if it does not pass. Before shipping, run:

```bash
fl-flexi check com.yourstudio.my_effect          # files, Python and venv, describe_effect
fl-flexi check com.yourstudio.my_effect --full   # then fl-flexi-test and test_effect
```

`--full` runs `fl-flexi-test` on random noise (`--synthetic`) at 1920x1080 and 3840x2160, so the
effect must run on noise at UHD with the weights it was installed with, not ones fetched on first
use. fl-diag runs the same tests and also:

- checks the manifest against the schema: run the validator (`references/manifest.md`)
- checks every reply against the schema: step 3's command with `--synthetic`
- on Linux, fails an effect that uses GPU memory during `describe_effect`

In 7.0.3 the full test cannot drive `file`-mode effects: they show FAIL ("Unsupported process
mode: file") even when they render correctly in Baselight. Tell your users to expect it.
