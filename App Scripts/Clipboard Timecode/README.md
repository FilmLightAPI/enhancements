# Clipboard Timecode

Jump cursor to Timecode in system clipboard

## How To Use

After highlighting a timecode and copying it into the clipboard, use the keyboard shortcut in Baselight:

- **Linux**: Win + Alt + V
- **Mac**: Ctrl + Opt + V

Or select *Jump To Clipboard Timecode* under the main *Baselight* or *Daylight* menu.

## Mac Installation

Place `jump_to_clipboard_timecode.py` into the */vol/.support/scripts* folder which is the same as /Library/Application Support/FilmLight/scripts


## Linux Installation

Linux requires the "xsel" command-line tool which is not included with FLOS 8. To install, run:

```
sudo dnf --enablerepo=epel install xsel
```

Then place `jump_to_clipboard_timecode.py` into the */vol/.support/scripts* folder which is the same as /usr/fl/scripts


Restart Baselight or select *Views > Scripts > <span style="display:inline-block; vertical-align: middle;">![Gear](/web/gear.png)</span> > Reload Scripts…* to load.