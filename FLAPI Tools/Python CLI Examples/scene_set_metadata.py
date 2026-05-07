import flapi
import time
import sys

if len(sys.argv) < 2:
    print( "No scene specified" );
    print( "Usage: %s host:job:scene" % sys.argv[0] )
    exit(1)

# Connect to FLAPI service
conn = flapi.Connection()
try:
    conn.connect()
except flapi.FLAPIException as ex:
    print(  "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

# Open the given scene
scene_path = conn.Scene.parse_path( sys.argv[1]  )

try:
    scene = conn.Scene.open_scene( scene_path )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Change name, clip and tape metadata for every shot
scene.start_delta( "Test set metadata")

nshots = scene.get_num_shots()
print( "Found %d shot(s)" % nshots )

if nshots > 0:
    shots = scene.get_shot_ids(0, nshots)
    for shot_ix, shot_inf in enumerate(shots):
        
        # Get Shot object for shot with the given ID
        shot = scene.get_shot(shot_inf.ShotId)
        
        # Set the Tape and Clip metadata
        new_md_values = {
            "name": "My new shot name",
            "clip": "My new Clip name",
            "tape": "My new Tape name"
        }

        shot.set_metadata( new_md_values )

        # Release Shot object
        shot.release()

scene.end_delta()
scene.save_scene()

print( "Updated %d shot(s)" % nshots )

scene.close_scene()
scene.release()

