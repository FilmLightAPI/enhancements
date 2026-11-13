# Example Temporal Average

Averages each frame with the frames before and after it, to show temporal inputs and RGBA images.

- The input declares `'temporal': [-1, 0, 1]`, so `run_generate` receives `src:-1`, `src:0`
  and `src:1`.
- Input and output are `4XFLOAT`: red, green, blue and alpha. Alpha is the image's opacity in
  Baselight, so an effect that takes RGBA must give back a meaningful alpha: here it is averaged
  with the colour, as FilmLight's own retiming effect does. Never put other data in alpha: a
  matte belongs in an effect of its own with a `1XFLOAT` output, like `person-matte`.
- At the start and end of a shot a neighbouring frame does not exist, so its key is missing
  or `None`. The effect averages only the frames it gets.
- Each frame is rendered on its own, in no guaranteed order, and the result depends only on
  that frame and its neighbours. Do not carry state from one `run_generate` call to the next.
