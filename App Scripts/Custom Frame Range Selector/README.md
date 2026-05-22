# Custom Frange Range Selector

Select multiple short frame ranges for rendering reference clips.

This script generates a list of frame ranges for selected shots that can be pasted directly into the render page.
It is useful for rendering short segments of a project to give a quick overview of the grade and its consistency.

Video Tutorial:
<video src='https://media.githubusercontent.com/media/FilmLightAPI/enhancements/refs/heads/main/App%20Scripts/Custom%20Frame%20Range%20Selector/Custom%20Frame%20Range%20Selector.mp4'>

## How To Use

Access **Custom Frame Range Selector** under the <span style="display:inline-block; vertical-align: middle;">![Gear](/web/gear.png)</span> menu in Shots view.

Modes:
 - Centered around Poster: Uses the shot's poster frame as center of the segments.
 - Centered around Middle: Uses always the mathematical center of the shot.
 - Starting/Ending: Segments are locked to the start or end of the shot.
 - Start and End Segments: Returns two segments per shot.
 - Across Cuts: Places the segments on the boundaries between shots.
 
The minimum shot length removes very short shots. Use 0 to include all shots.
 
The resulting frame range is copied to your clipboard and shown in an editable box

## Installation

Place `custom_frame_range_selector.py` into the */vol/.support/scripts* folder which is the same as
- **Linux:** /usr/fl/scripts
- **MacOS:** /Library/Application Support/FilmLight/scripts

Restart Baselight or select *Views > Scripts > <span style="display:inline-block; vertical-align: middle;">![Gear](/web/gear.png)</span> > Reload Scripts…* to load.