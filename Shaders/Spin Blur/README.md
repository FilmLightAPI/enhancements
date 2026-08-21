# Spin Blur

A radial blur that spins around a centre point

The effect can vaguely mimic the defocus of Petzval lenses.

![Screenshot](screenshot-1.jpg)

## Parameters

  - **Center (X/Y)**: Moves the focal point of the blur. The area around this point will remain sharp.
  - **Amount (Deg)**: The primary strength of the rotational blur, measured in degrees of rotation.
  - **Aspect Ratio**: Stretches the shape of the sharp center.
  - **Falloff Radius**: Controls the size of the sharp protected area in the center of the image.
  - **Falloff Softness**: Controls the transition distance from the sharp center to the fully blurred edges. Higher values create a very gradual roll-off.
  - **Chroma Spread**: Adds RGB color fringing to the blurred pixels. 
  - **Vignette Strength**: Darkens the edges of the image based on the blur falloff.
  - **Pre-Blur Factor**: Applies a pre-blur to the edges before rotating them, effectively reducing stepping artifacts.
  - **Samples**: The number of rotational texture lookups. If you see individual steps or ghosts in the blur at high Amounts, increase this value to smooth them out (or increase the Pre-Blur Factor to save performance)."

## Installation

Unzip and place files into the */vol/.support/shaders* folder which is the same as
- **Linux:** /usr/fl/shaders
- **MacOS:** /Library/Application Support/FilmLight/shaders