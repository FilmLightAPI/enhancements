# Import XML Marks

Imports markers from a Premiere Pro XML (Final Cut Pro format) file

![Screenshot](screenshot-1.jpg)

## How To Use

Select *Import XML Marks...* under the <span style="display:inline-block; vertical-align: middle;">![Gear](/web/gear.png)</span> icon in *Shots View*.

## Options

Mark Category
 - Select which Baselight category to assign the marks to.

Import Marks
 - All Marks: Imports both Sequence and Clip markers
 - Sequence Marks: Only imports markers on the main timeline
 - Clip Marks: Only imports markers embedded inside clips

Mark Type
 - Auto: Sequence Marks become Timeline Marks; Clip Marks become Shot Marks
 - Timeline Marks: Forces all markers to be Timeline Marks
 - Shot Marks: Forces all markers to be Shot Marks (falls back to Timeline if shot is missing)

Placement Mode
 - Absolute XML Timecode: Place marks based on Record Timecode
 - Scene Frame Number: Aligns the start of the XML with the start of the Baselight timeline
 - Relative to Cursor Position: Adds the marker offset to the current cursor position

## Installation

Place `ImportXMLMarks.py` into the */vol/.support/scripts* folder which is the same as
- **Linux:** /usr/fl/scripts
- **MacOS:** /Library/Application Support/FilmLight/scripts

Restart Baselight or select *Views > Scripts > <span style="display:inline-block; vertical-align: middle;">![Gear](/web/gear.png)</span> > Reload Scripts…* to load.