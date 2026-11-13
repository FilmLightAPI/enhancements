# Model weights

## Ship them with the effect

Render nodes are often offline, and Baselight runs effects as a user who cannot write to the
effect folder. So an effect must never download weights the first time it runs. Weights go into
the effect at install time and travel inside its package.

1. Keep weights out of your source repository. Fetch them with a script that checks a hash
   (`examples/person-matte/download_weights.py`), or from your own storage.
2. List them in the manifest's `weights`, mapping the path inside the installed effect to the
   path next to the `.flexi`:

   ```json
   "weights": { "weights/model.pth": "weights/model.pth" }
   ```

3. `fl-install-flexi-effect` copies them, and `fl-make-flexi-package` includes them in the
   package. The installer never replaces a weights file that is already installed: delete
   the installed effect folder before reinstalling with new weights.
4. Load them by a path relative to the effect's own file, never the current user's home:

   ```python
   WEIGHTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weights', 'model.pth')
   state = torch.load(WEIGHTS, map_location='cpu', mmap=True, weights_only=True)
   ```

## Libraries that download on their own

Hugging Face, `torch.hub`, `timm` and similar fetch weights into `~/.cache` by default. On a
render node that fails or fills the wrong disk. Point them at the effect folder and forbid
network access in the effect:

```python
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('HF_HOME', os.path.join(EFFECT_DIR, 'hf'))
torch.hub.set_dir(os.path.join(EFFECT_DIR, 'torchhub'))
```

and put the downloaded cache folders in `weights` so they ship with the effect.

## Format and size

- Prefer `safetensors` or a plain PyTorch state dict loaded with `weights_only=True`; do not
  unpickle arbitrary objects.
- Large weights are fine in a package, but each installed effect keeps its own copy. If several
  of your effects share a model, ship it once in one effect folder and load it from there, or
  combine the effects in one manifest.
- A manifest `weights` entry can be a tar archive, unpacked at install.

## Licences

Weights carry their own licence, often different from the code's, and sometimes restricted by
their training data. Check both before distributing an effect, and include them in the effect's
`LICENCE.md`.
