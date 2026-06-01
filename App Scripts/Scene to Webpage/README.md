# Scene to Webpage

Show the current scene's shot list on a webpage

This script adds a **"Show Scene as Webpage"** item to the Scene menu.
It reads every shot in the current scene, builds an HTML table, serves it from a
small background web server, and opens your browser at the URL.

This script uses standard libraries only - no accounts, no credentials, nothing to install. The
server runs on a daemon thread so the Baselight/Daylight UI never blocks, and
the page is read from a temp file per request, so re-running the menu item just
refreshes the already running server.

## Installation

Copy `scene_to_webpage.py` into the */vol/.support/scripts* folder which is the same as
- **Linux:** /usr/fl/scripts
- **MacOS:** /Library/Application Support/FilmLight/scripts

Restart Baselight or select *Views > Scripts > <span style="display:inline-block; vertical-align: middle;">![Gear](/web/gear.png)</span> > Reload Scripts…* to load.