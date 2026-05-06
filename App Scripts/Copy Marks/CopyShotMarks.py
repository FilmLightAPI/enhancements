# Updated Nov 3, 2025
# Place this script in /vol/.support/scripts/ for it to be run within the app.
# Click Views > Scripts > Gearbox > Reload Scripts… to re-load it. Monitor the Log tab for any errors.

# Access via the main Scene menu > Copy Shot Marks From Scene...

# This script will copy SHOT marks from one Baselight scene to another, matching shots based on CLIP or TAPE name.
# Both scenes must be open and the scene you want to copy INTO should be the active scene

import flapi
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class MyMark:
    frame:int
    category:str
    note:str
    matchby:str
    props:dict

lastSettings = {
    "MatchBy": "clip"
}

conn = flapi.Connection.get()

class MainDialog:
    def __init__(self, scenes):
        # Define items to show in dialog
        global lastSettings

        self.options: List[Dict[str, str]] = []
        for scene in scenes:
            self.options.append ({"Key": scene, "Text": scene})


        self.items = [
            flapi.DialogItem(Key="FromScene", Label="From Scene", Type=flapi.DIT_DROPDOWN, Options = self.options, Default = self.options[0]['Key']),
            flapi.DialogItem(Key="MatchBy", Label="Match By", Type=flapi.DIT_DROPDOWN, Options = [
                {"Key": "clip", "Text": "Clip"},
                {"Key": "tape", "Text": "Tape"},
                ], Default = 'clip'),
        ]

        # Create dialog, which will be shown later
        self.dialog = conn.DynamicDialog.create(
            "Copy Marks",
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

                    myMarks = []
                    global lastSettings
                    lastSettings['MatchBy'] = result['MatchBy']

                    # Lookup shots in source scene
                    nshots = fromScene.get_num_shots()
                    if nshots > 0:
                        shots = fromScene.get_shot_ids(0, nshots)
                        for shot_ix, shot_inf in enumerate(shots):

                            # Get Shot object for shot with the given ID
                            shot = fromScene.get_shot(shot_inf.ShotId)

                            # Get marks in shot
                            mark_ids = shot.get_mark_ids()
                            if len(mark_ids) > 0:
                                for ix,m in enumerate(mark_ids):
                                    mark = shot.get_mark(m)
                                    tn = shot.get_metadata([result['MatchBy']])
                                    if tn:
                                        tn = next(iter(tn.values()))

                                        myMarks.append( MyMark(
                                            frame = mark.get_source_frame(),
                                            category = mark.get_category(),
                                            note = mark.get_note_text(),
                                            matchby = tn,
                                            props = mark.get_properties()
                                        ))

                                    mark.release()
                            shot.release()

                    # Add marks to matching shots in current scene
                    scene.set_transient_write_lock_deltas(True)
                    scene.start_delta("Copy Marks")

                    try:
                        # Lookup shots in current scene
                        nshots = scene.get_num_shots()
                        if nshots > 0:
                            shots = scene.get_shot_ids(0, nshots)
                            for shot_ix, shot_inf in enumerate(shots):
                                # Get Shot object for shot with the given ID
                                shot = scene.get_shot(shot_inf.ShotId)
                                tn = shot.get_metadata([result['MatchBy']])
                                if tn:
                                    tn = next(iter(tn.values()))
                                    for m in myMarks:
                                        if m.matchby == tn:
                                            # Check for existing mark to avoid duplicates
                                            frameOffset = m.frame - shot.get_src_start_frame()
                                            skipDupe = False
                                            mark_ids = shot.get_mark_ids()
                                            if len(mark_ids) > 0:
                                                for ix,mx in enumerate(mark_ids):
                                                    mark = shot.get_mark(mx)
                                                    if mark.get_source_frame() == m.frame and mark.get_category() == m.category and mark.get_note_text() == m.note:
                                                        skipDupe = True
                                                    mark.release()
                                            
                                            if not skipDupe and m.frame >= shot.get_src_start_frame() and m.frame <= shot.get_src_end_frame():
                                                newMarkId = shot.add_mark( frameOffset, m.category, m.note )
                                                newMark = shot.get_mark(newMarkId)
                                                newMark.set_properties(m.props)
                                                newMark.release()
                                shot.release()

                    except flapi.FLAPIException as ex:
                        print( "Error adding marks: %s" % ex )

                    scene.end_delta()
                    scene.set_transient_write_lock_deltas(False)
                    fromScene.release()

            scene.release()



mainMenuItem1 = MainMenuItem( "Copy Shot Marks From Scene..." )
