# Place it in /vol/.support/scripts/ for it to be run within the app.
# Click Views>Scripts>Gearbox>Reload Scripts… to re-load it. Monitor the Log tab for any errors on load.

# Access via the main Baselight/Daylight menu > Find & Replace Paths

# Will perform batch find and replace on layer 0 audio paths

import flapi

conn = flapi.Connection.get()

class MainDialog:
    def __init__(self):
        # Define items to show in dialog
        self.items = [
            flapi.DialogItem(Key="Find", Label="Find", Type=flapi.DIT_STRING, Default = ""),
            flapi.DialogItem(Key="Replace", Label="Replace", Type=flapi.DIT_STRING, Default = ""),
            # Replacing image path not currently supported by FLAPI
            # flapi.DialogItem(Key="ReplaceImagePath", Label="Replace Image Paths", Type=flapi.DIT_TOGGLE, Default = 1),
            flapi.DialogItem(Key="ReplaceAudioPath", Label="Replace Audio Paths", Type=flapi.DIT_TOGGLE, Default = 1)
        ]

        # Create an empty dictionary for the default settings for the dialog
        self.settings = {
            "Find": "",
            "Replace": "",
            "ReplaceImagePath": 1,
            "ReplaceAudioPath": 1
        }

        # Create dialog, which will be shown later
        self.dialog = conn.DynamicDialog.create(
            "Find & Replace Paths",
            self.items,
            self.settings
        )

    def show(self):
        # Show the dialog modally
        #
        # If the user clicks OK, the settings from the dialog will be returned
        # as a dictionary
        #
        # If the user clicks Cancel, None will be returned.
        #
        # If you pass a negative width/height, it will add this width/height to the
        # default with of the contents of the dialog.
        #
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

    def handle_signal( self, sender, signal, args ):
        result = self.dialog.show()
        if result:
            # "OK" was clicked, process shots
            app = conn.Application.get()
            scene = app.get_current_scene()

            nshots = scene.get_num_shots()
            nshots_changed = 0
            if nshots > 0:
                shots = scene.get_shot_ids(0, nshots)
                scene.set_transient_write_lock_deltas(True)
                scene.start_delta("Replace Paths")
                for shot_ix, shot_inf in enumerate(shots):
                    #  get shot object
                    shot = scene.get_shot(shot_inf.ShotId)

                    if (result['ReplaceAudioPath'] == 1):
                        # replace audio path
                        try:
                            audioSettings = shot.get_audio_settings()
                            if audioSettings is not None:
                                filename = getattr(audioSettings, "Filename")
                                new_filename = filename.replace(result['Find'], result['Replace'])
                                if new_filename != filename:
                                    setattr(audioSettings, "Filename", new_filename)
                                    shot.set_audio_settings(audioSettings)
                                    nshots_changed += 1
                        except flapi.FLAPIException as ex:
                            print( "Error changing paths: %s" % ex )
                scene.end_delta()
                scene.set_transient_write_lock_deltas(False)
                scene.release()

            app.message_dialog(
                "Replace Done",
                "Replaced paths on %i shot%s" % (nshots_changed, 's' if nshots_changed > 1 else ''),
                ["OK"]
            )

mainMenuItem1 = MainMenuItem( "Find & Replace Paths" )
