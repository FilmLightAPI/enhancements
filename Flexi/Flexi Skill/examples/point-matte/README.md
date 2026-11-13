# Example Point Matte

A soft round matte around a point the user places in the viewer. It shows:

- a `point` param, drawn in the viewer with a `drawstyle`
- `fixed_image_size`: the effect always works on a 512×512 image, and Baselight scales the frame
  in and the matte back out
- `transform_to_fixed`, to map the point and the radius from frame pixels into that image
- `roi_sensitive`, so the matte is made from the whole frame whatever the viewer shows
- a 1-channel matte output

The radius is in frame pixels, so it is scaled by the transform's `Xx` like the point.

`fl-flexi-test` in 7.0.3 sends the point as its `default` list rather than in frame pixels;
`centre_in_fixed` accepts both. See `references/geometry.md` and `references/params-ui.md`.
