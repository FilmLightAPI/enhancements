# VRAM

Baselight shares each GPU between the grade, its caches and every Flexi effect on that GPU. It
asks each effect how much memory it needs, grants an amount, and can take it back. An effect
that uses more than it declared, or ignores a request to give memory back, makes other parts of
Baselight fail.

## The contract

1. **Nothing on the GPU until `set_vram_limit` grants memory.** No model loading, no
   `torch.cuda` calls, no `.to(device)` at import, in `__init__`, `describe_effect` or the
   query methods. Load the model in the first `run_generate`.
2. **`query_vram_requirement` returns `min_mb` and `max_mb`** for the given width, height and
   params. `width` and `height` are the output buffer's size (the `fixed_image_size` in that
   mode) or, when Baselight plans playback, the frame size; `n_in` counts input frames, temporal
   ones included. Both values are required. `max_mb` is what the effect would like; `min_mb` is
   the least it can still render with. Baselight grants a `limit_mb` between them, or less when
   memory is short.
3. **Stay within the grant.** The limit covers everything the effect process allocates on the
   GPU: weights, activations, temporaries, and on CUDA the context itself (several hundred MB
   that PyTorch's own counters do not show). It does not include the image buffers Baselight
   passes in.
4. **Give memory back when asked.** When `set_vram_limit` sends a limit below what the effect
   holds (often 0), free it before replying. If it cannot, return `'quit'`: `flexi.py` replies
   and exits the process, and Baselight starts a new one when needed. PyTorch cannot release a
   CUDA context, so on CUDA `'quit'` is the reliable answer to 0; on MPS, drop the model and
   call `torch.mps.empty_cache()`.

## Measuring

Measure; do not estimate. Run the effect's real inference path on the target GPU at the sizes
it will meet (HD, UHD, 4K DCI, and the largest your users have) and record the peak:

- **CUDA:** `torch.cuda.reset_peak_memory_stats()` before, `torch.cuda.max_memory_allocated()`
  after, plus the context: the drop in `torch.cuda.mem_get_info()[0]` from before the first CUDA
  call to after loading the model.
- **MPS:** there is no peak counter. Call `torch.mps.empty_cache()`, note
  `torch.mps.driver_allocated_memory()`, run, and take the growth plus
  `torch.mps.current_allocated_memory()`. Apple silicon memory is shared with the system, so
  treat these as approximate and use the CUDA figures where you have them.

Write a short script that loads and runs the model exactly as the effect does, at each size, and
prints these figures. `fl-flexi-test.py --json-summary` also reports the peak VRAM of each run. Fit
the results to `fixed + per-pixel × width × height` and declare them with 30–40% headroom.

## Adapting to the grant

An effect that can trade quality or speed for memory should declare the range and pick its
setting from the grant:

- `min_mb`: the cheapest way to render this frame (smaller inference size, tiles, fp16).
- `max_mb`: the best way.
- In `run_generate`, choose the best setting that fits `limit_mb`.

The person-matte example runs its model at a long side of 1024 when the grant allows and 512
when it does not. Tiling (rendering the frame in pieces and blending the overlaps) bounds memory
for models that work on local neighbourhoods; models that need the whole frame (segmentation,
depth) should reduce the inference size instead, and set `roi_sensitive`.

Test both ends. On Linux `fl-flexi-test.py` grants `max_mb`, so to test the low end make
`max_mb` temporarily equal to `min_mb`. With `shm` (every Mac) it grants an unlimited amount:
there, temporarily have `set_vram_limit` act as if it had been granted `min_mb`.

## Keeping the footprint small

- `torch.inference_mode()` (or `torch.no_grad()`) around inference; `get_torch_device()` turns
  autograd off for the thread that calls it.
- Load weights with `torch.load(path, map_location='cpu', mmap=True, weights_only=True)`: a
  multi-GPU machine runs one copy of the effect per GPU, and mmap lets them share one copy of the
  file in memory.
- fp16 or bf16 where the model tolerates it (check the output against fp32; bf16 is slow on
  Volta and earlier).
- Do not cache frames, features or results across `run_generate` calls beyond what the grant
  covers. `inputs_hash` lets you reuse work on the *same* inputs, which is what interactive
  grading on one frame needs.
- Free large temporaries before the next big allocation (`del`), and on MPS call
  `torch.mps.empty_cache()` after a frame if memory is tight.
