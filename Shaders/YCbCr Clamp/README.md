# YCbCr Clamp

Adjustable clamp to the image in Luma (Y) or RGB.

Model:
- **Y only - YCbCr**: Clamps only the Luma channel (preserves color).
- **RGB**: Clamps all RGB channels directly.

Settings:
- **Matrix**: Select conversion matrix (only used in YCbCr mode).
- **Low/High Clamp**: Thresholds in 10-bit integer units (0-1023).
- **Global Clamp**: Enable/disable the effect
- **Preview Clamp**: Highlights clamped areas in Orange (highlights) and Magenta (shadows)

## Installation

Unzip and place files into the */vol/.support/shaders* folder which is the same as
- **Linux:** /usr/fl/shaders
- **MacOS:** /Library/Application Support/FilmLight/shaders