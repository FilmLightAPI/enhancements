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

nshots = scene.get_num_shots()
print( "Found %d shot(s)" % nshots )
    
if nshots == 0:
    sys.exit(1)

shots = scene.get_shot_ids(0, nshots)
for shot_ix, shot_inf in enumerate(shots):
    print("Shot %d:" % (shot_ix + 1))
    
    # Get Shot object for shot with the given ID
    shot = scene.get_shot(shot_inf.ShotId)

    resources = None
    payload = None
    # Extract BLG resource
    try:
        resources = shot.get_blg_resources()
    except flapi.FLAPIException as ex:
        print( "Error extracting BLG resources: %s" % ex )

    try:
        payload = shot.get_blg_payload()
    except flapi.FLAPIException as ex:
        print( "Error extracting BLG payload: %s" % ex )

    
    # Write out resources and payload
    extensions = [".blgr", ".blgp"]
    for i,d in enumerate([resources, payload]):
        if d is not None:
            try: 
                path = sys.argv[2]+"/shot_"+str(shot_ix+1)+extensions[i]
                with open(path,'w') as f:
                    f.write(d)
                print("\nWrote: %s" % path)
            except Exception as ex:
                print( "Error writing %s: %s" % (path, ex) )

scene.release()
