import sys
import flapi

if len(sys.argv) < 2:
    print( "usage: insert_seq.py <path_to_sequence> [<start frame> <end frame>]" )
    sys.exit(1)

conn = flapi.Connection("localhost")

try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

jm = conn.JobManager
if not jm.job_exists("localhost", "flapi"):
    jm.create_job( "localhost", "flapi" )

if jm.scene_exists( "localhost", "flapi", "insert_test" ):
    jm.delete_scene( "localhost", "flapi", "insert_test", ignoreLocks=1 )

sceneOptions = {
    "format": "HD 1920x1080",
    "colourspace": "FilmLight_TLog_EGamut",
    "frame_rate": 24.0,
    "field_order" : flapi.FIELDORDER_PROGRESSIVE
}

scene_path = flapi.ScenePath({ "Host": "localhost", "Job": "flapi", "Scene": "insert_test"})

try:
    scene = conn.Scene.new_scene( scene_path, sceneOptions )
except flapi.FLAPIException as ex:
    print( "Error creating scene: %s" % ex )
    sys.exit(1)

# Create SequenceDescriptor for the given path/frame-range
template = sys.argv[1]
if len(sys.argv) > 2:
    startFrame = int( sys.argv[2], 10 )
    endFrame = int( sys.argv[3], 10 )
else:
    startFrame = None
    endFrame = None

seqs = conn.SequenceDescriptor.get_for_template( template, None, None )
if len(seqs)==0:
    print( "Cannot find SequenceDescriptor for " + template )
    sys.exit(1)

# Insert SequenceDescriptor into Scene, producing a Shot object
scene.start_delta("Insert Sequence(s)")

shots = []
for seq in seqs:
    shot = scene.insert_sequence( seq, flapi.INSERT_END, None, None, None )
    shots.append(shot)
    seq.release()

scene.end_delta()

# Print out some info about the sequence we just inserted
for shot in shots:
    md = shot.get_metadata_strings( [ "clip", "tape", "srctc" ] )
    for mdk in md:
        print( "    %s: %s" % (mdk, md[mdk]) )

# Release Shot objects
for shot in shots:
    shot.release()

# Save changes
scene.save_scene()
scene.close_scene()
scene.release()

