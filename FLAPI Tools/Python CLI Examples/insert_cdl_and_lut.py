import flapi
import time
import sys

if len(sys.argv) < 2:
    print( "No scene specified" );
    print( "Usage: %s host:job:scene [optional-path-to-lut]"  % sys.argv[0] )
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
    scene.start_delta("Inserting CDLs")
    shots = scene.get_shot_ids(0, nshots)
    for shot_ix, shot_inf in enumerate(shots):
        print("Shot %d:" % shot_ix)
        
        # Get Shot object for shot with the given ID
        shot = scene.get_shot(shot_inf.ShotId)
        
        if (len(sys.argv) > 2):
            print("Inserting LUT %s" % sys.argv[2])
            shot.insert_truelight_layer(sys.argv[2])

        if (shot_ix % 2 == 1):
            print("inserting cdl layer below")
            shot.insert_cdl_layer([1.5140, 1.5150, 1.5160, -0.0823, -0.1405, -0.1236, 0.77, 0.78, 0.79, 0.8])
        else:
            print("inserting cdl layer above")
            shot.insert_cdl_layer_above([1.5140, 1.5150, 1.5160, -0.0823, -0.1405, -0.1236, 0.77, 0.78, 0.79, 0.8])
        # Release Shot object
        shot.release()

    scene.end_delta()

scene.save_scene()
scene.close_scene()
scene.release()

