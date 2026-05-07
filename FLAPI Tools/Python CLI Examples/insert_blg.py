import flapi
import time
import sys

if len(sys.argv) < 3:
    print( "Scene and blg_path not specified" );
    print( "Usage: %s host:job:scene blg_path" % sys.argv[0] )
    exit(1)

# Connect o  FLAPI
conn = flapi.Connection()
try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

# Open the given scene
scene_path = conn.Scene.parse_path( sys.argv[1]  )

try:
    scene = conn.Scene.open_scene( scene_path )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Lookup shots
nshots = scene.get_num_shots()
print( "Found %d shot(s)" % nshots )

if nshots > 0:
    scene.start_delta("Inserting BLGs")
    shots = scene.get_shot_ids(0, nshots)
    for shot_ix, shot_inf in enumerate(shots):
        print("Shot %d:" % shot_ix)
        
        # Get Shot object for shot with the given ID
        shot = scene.get_shot(shot_inf.ShotId)
	
        shot.insert_blg_stack(sys.argv[2])
        
        # Release Shot object
        shot.release()

    scene.end_delta()

scene.save_scene()
scene.close_scene()
scene.release()

