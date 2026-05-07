import flapi
import time
import sys
import os

if len(sys.argv) < 3:
    print( "Usage: %s <scene> <resource_dir>" % sys.argv[0] )
    print(" Note: resource_dir must be an absolute path")
    exit(1)

if not os.path.isdir(sys.argv[2]):
    print("You did not provide a valid resource directory") 

# Connect to FLAPI
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
print( "\nFound %d shot(s)" % nshots )
if nshots == 0:
    sys.exit(1)

scene.start_delta("Inserting BLGs")
shots = scene.get_shot_ids(0, nshots)
for shot_ix, shot_inf in enumerate(shots):
    print("Shot %d:" % (shot_ix + 1))
    
    # Get Shot object for shot with the given ID
    shot = scene.get_shot(shot_inf.ShotId)

    # try to load the BLG resources and payload 
    resources = None
    try: 
        path = sys.argv[2]+"/shot_"+str(shot_ix+1)+".blgr"
        f = open(path)
        resources = f.read()
        f.close()
        print("Opened BLG resources from: %s" % path)
    except Exception as ex:
        print( "Error opening BLG resources file: %s" % ex )

    payload = None
    try: 
        path = sys.argv[2]+"/shot_"+str(shot_ix+1)+".blgp"
        f = open(path)
        payload = f.read()
        f.close()
        print("Opened BLG payload from: %s" % path)
    except Exception as ex:
        print( "Error opening BLG payload: %s" % ex )
    if (resources is not None) and (payload is not None):
        # Apply resources and payload to shot
        try:
            shot.apply_blg_payload(payload, resources)
            print("Successfully applied BLG resources and payload")
        except flapi.FLAPIException as ex:
            print( "Error applying BLG resources or payload: %s" % ex )
            sys.exit(1)
    
    # Release Shot object
    shot.release()

scene.end_delta()

scene.save_scene()
scene.close_scene()
scene.release()
