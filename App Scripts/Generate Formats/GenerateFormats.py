# Updated May 28, 2026
# Place this script in /vol/.support/scripts/ for it to be run within the app.
# Click Views > Scripts > Gearbox > Reload Scripts… to re-load it. Monitor the Log tab for any errors.

# This script will generate Formats for your current scene
# Access via the main Baselight menu > Generate Formats...

# TODO: Deal with working formats that aren't 1:1 ratio

import flapi
import re
from typing import Dict, List

# Default settings (and hold last settings used this session)
lastSettings = {
    "Fit": "Fit Width",
    "Prefix": "GF",
    "Override": 0
}

conn = flapi.Connection.get()


class MainDialog:
    def __init__(self):
        # Define options for "Mapping" pulldown menu
        self.options: List[Dict[str, str]] = [
            {"Key": "Width", "Text": "Fit Width"},
            {"Key": "Height", "Text": "Fit Height"},
            {"Key": "Inside", "Text": "Fit All Inside"},
            {"Key": "Outside", "Text": "Fill Frame"},
        ]

        # Define items to show in dialog
        self.items = [
            flapi.DialogItem(Key="Fit", Label="Mapping", Type=flapi.DIT_DROPDOWN, Options = self.options, Default = self.options[0]['Key']),
            flapi.DialogItem(Key="Prefix", Label="Prefix name for generated formats", Type=flapi.DIT_STRING, Default = "GF"),
            flapi.DialogItem(Key="Override", Label="Replace/Override assigned formats", Type=flapi.DIT_TOGGLE, Default = 0)
        ]

        # Create dialog, which will be shown later
        self.dialog = conn.DynamicDialog.create(
            "Generate Formats",
            self.items,
            lastSettings
        )

    def show(self):
        # Show the dialog modally
        return self.dialog.show_modal(-200, -25)

class MainMenuItem:
    def __init__(self, message):
        # Save variables in this object instance
        self.message = message

        # Register menu item with the application
        self.menuItem = conn.MenuItem.create( self.message )
        self.menuItem.register( flapi.MENULOCATION_APP_MENU )
        self.menuItem.connect( "MenuItemSelected", self.handle_signal )
        
        # Create the dialog, which we will use later
        self.dialog = MainDialog()
        
    def generate_formats(self, scene, options):
        prefix = options["Prefix"]
        
        # Get the name of the scene's workiing format
        scene_settings = scene.get_scene_settings()
        working_format_name = scene_settings.get(['WorkingFormat'])['WorkingFormat']
        
        # Get the FLAPI Format object of work working format and
        # FormatInfo for resolution and pixel aspect ratio
        scene_formats = scene.get_formats()
        working_format = scene_formats.get_format(working_format_name)
        working_format_res = working_format.get_resolution()
                
        # Store the Working Format mappings in a dict
        # "key" is the format name
        # "value" is a FLAPI FormatMapping Object
        mappings = {}
        mapping_names = working_format.get_mapping_names()
        for name in mapping_names:
            mappings[name] = working_format.get_mapping(name)

        nshots = scene.get_num_shots()
        if nshots > 0:
            format_count = 0
            shots = scene.get_shot_ids(0, nshots)
            for shot_ix, shot_inf in enumerate(shots):
                # Get Shot object for shot with the given ID
                shot = scene.get_shot(shot_inf.ShotId)
                try:
                    format_name = shot.get_input_format()
                except flapi.FLAPIException:
                    # Blanks and other generated sources won't have a format, skip them
                    continue
                                
                # check if this shot has an auto-generated format in parenthesis
                match = re.search(r"\((\d+)×(\d+)\)", format_name)
                if match or options["Override"] == 1:
                    if options["Override"] == 1:
                        old_format = scene_formats.get_format(format_name)
                        old_format_res = old_format.get_resolution()
                        width = old_format_res.Width
                        height = old_format_res.Height
                        ratio = old_format_res.PixelAspectRatio
                        # Remove ".0" from ratio if it's an integer
                        if ratio.is_integer():
                            ratio = int(ratio)
                        new_format_name = f"{prefix} {width}x{height}"
                        if ratio != 1.0:
                            new_format_name += f" [{ratio}:1]"
                    else:
                        width = int(match.group(1))
                        height = int(match.group(2))
                        ratio = 1.0
                        new_format_name = f"{prefix} {width}x{height}"
                        match2 = re.search(r"\[(\d+):(\d+)\]", format_name)
                        if match2:                                    
                            ratio = float(match2.group(1)) / float(match2.group(2))
                            new_format_name += ' ' + match2.group(0)
                    
                    if new_format_name not in mappings:
                        # Make a new format and map it
                        new_format = scene_formats.add_format( new_format_name, "Auto Generated Format", width, height, ratio )
                        mappings[new_format_name] = new_format
                        format_count += 1
                        
                        if options["Fit"] == "Inside":
                            new_format.add_mapping (working_format_name, flapi.FormatMapping( inside = 1 ))
                        elif options["Fit"] == "Outside":
                            new_format.add_mapping (working_format_name, flapi.FormatMapping( inside = 0 ))
                        elif options["Fit"] == "Width":
                            scale = working_format_res.Width / width
                            offset_x = 0.0
                            offset_y = (working_format_res.Height - (height * (scale / ratio))) / 2
                            new_format.add_mapping (working_format_name, flapi.FormatMapping( sx=scale, sy=scale / ratio, tx=offset_x, ty=offset_y ))
                        elif options["Fit"] == "Height":
                            scale = working_format_res.Height / height * ratio
                            offset_x = (working_format_res.Width - (width * scale)) / 2
                            offset_y = 0.0
                            new_format.add_mapping (working_format_name, flapi.FormatMapping( sx=scale, sy=scale / ratio, tx=offset_x, ty=offset_y ))

                    # Assign format to shot
                    shot.set_input_format(new_format_name)
                    
                shot.release()
            
            print(f"Created {format_count} new format mappings.", flush=True)

        scene_formats.release

    def handle_signal( self, sender, signal, args ):
        app = conn.Application.get()
        scene = app.get_current_scene()
        if scene is not None:
            result = self.dialog.show()
            if result:
                global lastSettings
                lastSettings["Fit"] = result["Fit"]
                lastSettings["Prefix"] = result["Prefix"]
                lastSettings["Override"] = result["Override"]
                
                scene.set_transient_write_lock_deltas(True)
                scene.start_delta("Generate Formats")
                
                try:
                    self.generate_formats(scene, result)
                except flapi.FLAPIException as ex:
                    print(f"ERROR: {ex}", flush=True)
                    
                scene.end_delta()
                scene.set_transient_write_lock_deltas(False)

            scene.release()


mainMenuItem1 = MainMenuItem( "Generate Formats" )
