# Updated May 18, 2026
# Place this script in /vol/.support/scripts/ for it to be run within the app.
# Click Views > Scripts > Gearbox > Reload Scripts… to re-load it. Monitor the Log tab for any errors.

# Access via the Shots view: Gear > Remove Zero Padding

# This script removes zero padding from shot and take metadata

import flapi
import traceback

conn = flapi.Connection.get()


class ShotsMenuItem:
    def __init__(self, message):
        # Save variables in this object instance
        self.message = message

        # Register menu item with the application
        self.menuItem = conn.MenuItem.create(self.message)
        self.menuItem.register(flapi.MENULOCATION_SHOT_VIEW)
        self.menuItem.connect("MenuItemSelected", self.handle_signal)

    def handle_signal(self, sender, signal, args):
        app = conn.Application.get()
        scene = app.get_current_scene()
        nshots = scene.get_num_shots()

        if nshots > 0:
            shots = scene.get_shot_ids(0, nshots)
            scene.set_transient_write_lock_deltas(True)
            scene.start_delta("Remove Zero Padding")
            
            # Remove leading '0's from scene and take metadata.
            # Wrapped with try/except to avoid locking the app with a
            # "delta in progress" error if something goes wrong
            try:            
                for shot_ix, shot_inf in enumerate(shots):
                    shot = scene.get_shot(shot_inf.ShotId)

                    shot_md = shot.get_metadata_strings({'scene', 'take'})
                    shot.set_metadata ({'scene': shot_md['scene'].lstrip('0'), 'take': shot_md['take'].lstrip('0')})

                    shot.release()
            except Exception:
                traceback.print_exc()
                
            scene.end_delta()
            scene.set_transient_write_lock_deltas(False)
        
        scene.release()


shotMenuItem1 = ShotsMenuItem("Remove Zero Padding")
