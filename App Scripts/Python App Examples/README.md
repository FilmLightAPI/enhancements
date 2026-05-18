# Python APP Examples

Basic FLAPI examples for Baselight/Daylight GUI writen in Python

- **cursor_info_in_list_dialog.py** Makes a ListDialog, triggerable by a MenuItem, that displays info about the app's cursors.
- **dialog_object_items_showcase.py** Creates a dialog that allows user to individually view all supported DialogItem types.
- **dialog_object_with_timer.py** Define a dialog class which uses DynamicDialog to present a dialog to the user. It uses the timer callback to update asynchronously.
- **dialog_object.py** Make a simple DynamicDialog tied to a MenuItem.
- **list_dialog.py** Make a ListDialog, triggerable by a MenuItem, which is enabled only if a scene is open
- **menu_object.py** Creates MenuItems with counters that increment when clicked
- **message_dialog_on_application_signal.py** Displays a MessageDialog whenever a scene is opened
- **nested_menu_items.py** An example of nested menus
- **progress_bar.py** Displays a ProgressBar triggered by a MenuItem
- **select_scene_and_open.py** shows a dialog with a scene picker, then opens the selected scene in the Baselight timeline (requires 7.0.1 or later).


## Installation

Place the script(s) you want to test into the */vol/.support/scripts* folder which is the same as
- **Linux:** /usr/fl/scripts
- **MacOS:** /Library/Application Support/FilmLight/scripts

Restart Baselight or select *Views > Scripts > <span style="display:inline-block; vertical-align: middle;">![Gear](/web/gear.png)</span> > Reload Scripts…* to load.

## Changelog

May 18, 2026 - Added select_scene_and_open.py