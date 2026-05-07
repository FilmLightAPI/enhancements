import flapi
import time
import sys
import os

if len(sys.argv) < 4:
    print( "Absolute_blg_input_path, absolute_resources_output_path and/or absolute_payload_output_path not specified" );
    print( "Usage: %s absolute_blg_input_path absolute_resources_output_path absolute_payload_output_path" % sys.argv[0] )
    exit(1)

if not os.path.isfile(sys.argv[1]):
    print("You did not provide a valid path to an input BLG file")

if not os.path.isdir(os.path.dirname(sys.argv[2])):
    print("You did not provide a valid output directory for the resources file")

if not os.path.isdir(os.path.dirname(sys.argv[3])):
    print("You did not provide a valid output directory for the payload file")

if os.path.basename(sys.argv[2]) is None:
    print("You did not provide a valid filename for the BLG resources file (e.g., blg_resources.blgr")

if os.path.basename(sys.argv[3]) is None:
    print("You did not provide a valid filename for the BLG payload file (e.g., blg_payload.blgp")

# Connect o  FLAPI
conn = flapi.Connection()
try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

# Define scene options
sceneOptions = {
    "format": "HD 1920x1080",
    "colourspace": "FilmLight_TLog_EGamut",
    "frame_rate": 24.0,
    "field_order" : flapi.FIELDORDER_PROGRESSIVE
}

# Create a temporary scene
try:
    scene = conn.Scene.temporary_scene (sceneOptions)
except flapi.FLAPIException as ex:
    print( "Error creating temporary scene: %s" % ex )
    sys.exit(1)

# Load BLG as Sequence Descriptor
try:
    sequence = conn.SequenceDescriptor.get_for_file(sys.argv[1])
except flapi.FLAPIException as ex:
    print( "Error loading BLG as Sequence Descriptor: %s" % ex )
    sys.exit(1)
    
# Insert results into scene
if sequence.has_blg(): # Filter in only the BLGs
    scene.start_delta("Insert Sequence(s)")
    shot = scene.insert_sequence(sequence, flapi.INSERT_END, None, None, None)

    # Extract BLG resource
    try:
        resources = shot.get_blg_resources()
        print("\nExtracted resources: %s" % resources)
    except flapi.FLAPIException as ex:
        print( "\nError extracting BLG resources: %s" % ex )

    try:
        payload = shot.get_blg_payload()
        print("\nExtracted payload: %s" % payload)
    except flapi.FLAPIException as ex:
        print( "\nError extracting BLG paylaod: %s" % ex )

    # Write out resources and payload
    for i,d in enumerate([resources, payload]):
        try: 
            with open(sys.argv[i+2],'w') as f:
                f.write(d)
            print("\nWrote: %s" % sys.argv[i+2])
        except Exception as ex:
            print( "Error writing %s: %s" % (sys.argv[i+2], ex) )

scene.end_delta()
scene.release()