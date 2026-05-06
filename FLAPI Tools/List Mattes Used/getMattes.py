import flapi
import time
import sys

if len(sys.argv) < 2:
    print( "No scene specified" );
    print( "Usage: %s host:job:scene" % sys.argv[0] )
    exit(1)


# Connect to FLAPI
conn = flapi.Connection()
conn.connect()

# Open the given scene
scene_path = conn.Scene.parse_path( sys.argv[1]  )

try:
    scene = conn.Scene.open_scene( scene_path, { flapi.OPENFLAG_READ_ONLY } )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Lookup shots
nshots = scene.get_num_shots()
print( "Found %d shot(s)" % nshots )

if nshots > 0:
    shots = scene.get_shot_ids(0, nshots)
    for shot_ix, shot_inf in enumerate(shots):
        
        # Get Shot object for shot with the given ID
        shot = scene.get_shot(shot_inf.ShotId)
        
        # Get any matte channels referenced 
        shot_chans = shot.get_matte_references()
        if shot_chans:
            filename = shot.get_metadata_strings([ "filename" ])["filename"]
            print(f"Shot {shot_ix}: {filename}")
            print(f"Channels: {shot_chans}")

        # Release Shot object
        shot.release()

scene.close_scene()
scene.release()

