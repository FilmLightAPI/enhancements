# Updated July 14, 2025
# Place this script in /vol/.support/scripts/ for it to be run within the app.
# Click Views > Scripts > Gearbox > Reload Scripts… to re-load it. Monitor the Log tab for any errors.

# Access via the main Scene menu > Copy Marks From Scene...

# This script will copy TIMELINE marks from one Baselight scene to another.
# Both scenes must be open and the scene you want to copy INTO should be the active scene

import flapi
from typing import Dict, List

conn = flapi.Connection.get()

class MainDialog:
    def __init__(self, scenes):
        # Define items to show in dialog
        self.options: List[Dict[str, str]] = []
        for scene in scenes:
            self.options.append ({"Key": scene, "Text": scene})

        self.items = [
            flapi.DialogItem(Key="FromScene", Label="From Scene", Type=flapi.DIT_DROPDOWN, Options = self.options, Default = self.options[0]['Key']),
            flapi.DialogItem(Key="Offset", Label="Frame Offset", Type=flapi.DIT_INTEGER, IntMin = 0, IntMax=1000000, Default = 0),
        ]

        # Create a dictionary for the default settings for the dialog
        self.settings = {
            "Offset" : 0
        }

        # Create dialog, which will be shown later
        self.dialog = conn.DynamicDialog.create(
            "Copy Marks",
            self.items,
            self.settings
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
        self.menuItem.register( flapi.MENULOCATION_SCENE_MENU )
        self.menuItem.connect( "MenuItemSelected", self.handle_signal )

    def handle_signal( self, sender, signal, args ):
        app = conn.Application.get()
        scene = app.get_current_scene()
        if scene is not None:
            # Get a list of open scenes so user can choose one to copy marks from
            # Excludes scene names containing "baselight_gallery", this could cause problems if
            # users set their gallery job folder to a different name
            # but there is not currently a FLAPI method for reading that preference
            openScenes = app.get_open_scene_names()
            openScenes.remove(app.get_current_scene_name())
            sceneList = []
            for s in openScenes:
                if ":baselight_gallery" not in s:
                    sceneList.append(s)

            if len(sceneList) < 1:
                app.message_dialog('ERROR', "Please open the scenes you wish to copy marks from and to.", ["OK"])
            else:
                self.dialog = MainDialog(sceneList)
                result = self.dialog.show()
                if result:
                    # "OK" was clicked, process marks
                    fromScene = app.get_scene_by_name(result['FromScene'])
                    tlMarks = fromScene.get_mark_ids()

                    scene.set_transient_write_lock_deltas(True)
                    scene.start_delta("Copy Marks")

                    try:
                        # Copy Timeline Marks
                        # Known Limitation: Marks with no media underneath them are skipped by get_mark_ids
                        for mid in tlMarks:
                            m = fromScene.get_mark(mid)
                            props = m.get_properties()
                            newMarkId = scene.add_mark( m.get_record_frame() + result['Offset'], m.get_category(), m.get_note_text() )
                            m.release()
                            newMark = scene.get_mark(newMarkId)
                            newMark.set_properties(props)
                            newMark.release()

                    except flapi.FLAPIException as ex:
                        print( "Error adding mark: %s" % ex )

                    scene.end_delta()
                    scene.set_transient_write_lock_deltas(False)
                    fromScene.release()

            scene.release()



mainMenuItem1 = MainMenuItem( "Copy Timeline Marks From Scene..." )
