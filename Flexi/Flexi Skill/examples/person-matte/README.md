# Example Person Matte

A soft matte of the people in the frame, from a pretrained segmentation model.

It shows what a real model effect needs:

- **Weights** are not in this folder. `download_weights.py` fetches them and checks their hash;
  the manifest's `weights` section installs and packages them; the effect loads them with
  `torch.load(..., mmap=True, weights_only=True)` from its own folder.
- **Normalised input**: the input's `normalise` makes Baselight apply the model's ImageNet
  mean and standard deviation, and `input_colour_space` gives it display sRGB.
- **A matte output**: `1XFLOAT`.
- **VRAM**: measured on CUDA (see `references/vram.md`); `query_vram_requirement` declares
  `min_mb` (inference at a long side of 512) and `max_mb` (1024), and `run_generate` picks the
  size the grant allows. `set_vram_limit(0)` returns `'quit'` on CUDA and empties the cache on
  MPS.
- **Portable resizing**: pooling by a whole factor, then bilinear, which works on CUDA, Apple
  silicon and Intel Macs (PyTorch 2.2 on MPS has no antialiased resize).

```bash
python3 download_weights.py          # or the Flexi platform's python3
fl-install-flexi-effect -t ~/flexi-scratch com.example.person_matte.v1.flexi
```

The model is torchvision's DeepLabV3 with a MobileNetV3 backbone. Check the licence of its weights
before using them in a product; see `LICENCE.md`.
