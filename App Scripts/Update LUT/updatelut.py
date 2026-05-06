# Place this script in /vol/.support/scripts/ for it to be run within the app.
# Click Views > Scripts > Gearbox > Reload Scripts… to re-load it. Monitor the Log tab for any errors.

# Access via the main Scene menu > Update LUTs

import flapi

LUT_DIRECTORY = "/Library/Truelight/cubes"
LUT_LAYER_NUM = 1
LUT_NAME = "test.cub"

conn = flapi.Connection.get()

class SceneMenuItem:

    ##### __init__
    # Initialize menu item
    #
    def __init__(self, message):
        # Save variables in this object instance
        self.message = message

        # Register menu item with the application
        self.menu_item = conn.MenuItem.create( self.message )
        self.menu_item.register( flapi.MENULOCATION_SCENE_MENU )
        self.menu_item.connect( "MenuItemSelected", self.handle_signal )

    ##### handle_signal
    # Respond to "Update LUTs" being selected from menu
    #
    def handle_signal( self, sender, signal, args ):
        app = conn.Application.get()
        scene = app.get_current_scene()

        scene.set_transient_write_lock_deltas(True)
        scene.start_delta( "Update LUTs" )

        # Set LUT metadata for shots
        num_shots = scene.get_num_shots()
        if num_shots > 0:
            shots = scene.get_shot_ids(0, num_shots)
            for shot_ix, shot_inf in enumerate(shots):
                shot = scene.get_shot(shot_inf.ShotId)
                shot.set_metadata( {"lut": LUT_NAME} )
                shot.release()

        # Do a Multi paste to apply LUTs
        try:
            mpSettings = flapi.MultiPasteSettings()
            mpSettings.Source = flapi.MULTIPASTE_SOURCE_LUT
            mpSettings.DestSelection = flapi.MULTIPASTE_DESTSELECTION_SELECTEDSHOTS
            mpSettings.MatchBy = [ flapi.MULTIPASTE_MATCHBY_LUT, flapi.MULTIPASTE_MATCHBY_ALWAYSMATCH ]
            mpSettings.LUTDirectory = LUT_DIRECTORY
            mpSettings.LUTLayerNum = LUT_LAYER_NUM
            mp = conn.MultiPaste.create()
            numShots = mp.multi_paste( scene, mpSettings )
        except Exception as ex:
            print( "MultiPaste failed: %s" % ex, flush=True)

        scene.end_delta()
        scene.set_transient_write_lock_deltas(False)

        scene.release()
        print ("Done Updateing LUTS.", flush=True)


sceneMenuItem1 = SceneMenuItem( "Update LUTs" )
