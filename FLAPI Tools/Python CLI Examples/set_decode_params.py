"""
Run this script on a scene with raw camera shots, it will print a list of
available decode parameters and apply changes to some.
"""


import flapi
import sys

if len(sys.argv) < 2:
    print( "No scene specified" )
    print( "Usage: %s host:job:scene" % sys.argv[0] )
    exit(1)

# Connect o  FLAPI
conn = flapi.Connection()
try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

# Open the given scene
scene_path = conn.Scene.parse_path( sys.argv[1] )

try:
    scene = conn.Scene.open_scene( scene_path )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Lookup shots
nshots = scene.get_num_shots()
print( "Found %d shot(s)" % nshots )

if nshots > 0:
    scene.start_delta("Setting Decode Params")
    shots = scene.get_shot_ids(0, nshots)
    for shot_ix, shot_inf in enumerate(shots):
        print("Shot %d:" % shot_ix)
        
        # Get Shot object for shot with the given ID
        shot = scene.get_shot(shot_inf.ShotId)
                
        codec = shot.get_codec()
        print( "Codec: %s" % codec )
        if codec is None:
            continue
        
        decode_type = conn.Shot.get_decode_parameter_type_for_codec(codec)
        print( "decode_type: %s" % decode_type )
        if decode_type is None:
            continue
        
        param_defs = conn.Shot.get_decode_parameter_definitions(decode_type)
        if param_defs is not None:

            # Print out the parameter definitions for this code type..
            print("-----------------------------------------------------------")
            print("Decode Parameter Definitions for %s:" % codec)
            for param_def in param_defs:
                print("%s:" % param_def["Parameter"])
                print("    Type: %s" % param_def["Type"])
                if hasattr(param_def, "Label"):
                    print("    %s" % param_def["Label"].encode('utf-8'))
                print("    Default: %s" % str(param_def["Default"]))
                if hasattr(param_def, "Min"):
                    print("    Min: %s" % str(param_def["Min"]))
                if hasattr(param_def, "Max"):
                    print("    Max: %s" % str(param_def["Max"]))
                if hasattr(param_def, "Choices") and param_def["Choices"] is not None:
                    print("    Choices:")
                    for choice in param_def["Choices"]:
                        print("        %s: %s" % (choice["Value"], choice["Label"]))
                print("")
            
            # Squirrel away the current decode parameters for the shot, so we
            # can compare them later..
            old_params = shot.get_decode_parameters()
            
            # Set some parameters..
            params = None
            if codec == "R3D": 
                params = {"iso" : 3200, "exposure_compensation": 3.5}
            elif codec == "ARRIRAW":
                params = {"blueTuning" : 75.0, "debayer": 4, "doAlexa.iso": 500}
            elif codec == "Sonyraw":
                params = {"doSony.useEI" : 0, "kelvin": 9000, "doSony.ei": 700}
                
            if params is not None:
                shot.set_decode_parameters(params)

            # Test unknown parameter..
            try:
                params = {"will_not_exist" : 666}
                shot.set_decode_parameters(params)
            except flapi.FLAPIException as ex:
                print("Correctly detected invalid parameter. %s" % ex)
            
            # Work out if the set_decode_parameters call did something..
            new_params = shot.get_decode_parameters()
            changed = { }
            for p in new_params:
                if new_params[p] != old_params[p]:
                    print(f"{p} changed from {new_params[p]} to {old_params[p]}\n")
            
        # Release Shot object
        shot.release()

    scene.end_delta()

scene.save_scene()
scene.close_scene()
scene.release()

