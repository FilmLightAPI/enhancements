import sys
import flapi

if len(sys.argv) < 3 or len(sys.argv) % 2 == 0:
    print( "usage: insert_leaf_operators <type> <duration> [<type> <duration>] ... " )
    print("     <type> = one of Blank, Bars, Text" )
    print("     <duration> = duration in frames")
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

if jm.scene_exists( "localhost", "flapi", "insert_operators_test" ):
    jm.delete_scene( "localhost", "flapi", "insert_operators_test", ignoreLocks=1 )

sceneOptions = {
    "format": "HD 1920x1080",
    "colourspace": "FilmLight_TLog_EGamut",
    "frame_rate": 24.0,
    "field_order" : flapi.FIELDORDER_PROGRESSIVE
}

scene_path = flapi.ScenePath({ "Host": "localhost", "Job": "flapi", "Scene": "insert_operators_test"})

try:
    scene = conn.Scene.new_scene( scene_path, sceneOptions )
except flapi.FLAPIException as ex:
    print( "Error creating scene: %s" % ex )
    sys.exit(1)

# Insert operators into Scene
scene.start_delta("Insert Operators via FLAPI")

idx = 1
while (idx < len(sys.argv)):
    op_type = sys.argv[idx]
    duration = sys.argv[idx+1]
    idx+=2
    shot = None
    if (op_type == "Bars"):
        shot = scene.insert_bars(flapi.OPERATOR_BARS_TYPE_ITU2111_PQ, duration, flapi.INSERT_END, None, None);
    elif (op_type == "Blank"):
        shot = scene.insert_blank(0.9, 0.1, 0.1, duration, flapi.INSERT_END, None, None);
    elif (op_type == "Text"):
        shot = scene.insert_text("The quick brown fox", duration, flapi.INSERT_END, None);

    if (shot != None):
        shot.release()
    else:
        print("Unknown type %s (ignored)" % op_type)

scene.end_delta()

# Save changes
scene.save_scene()
scene.close_scene()
scene.release()

