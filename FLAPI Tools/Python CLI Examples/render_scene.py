import flapi
import sys
import time

if len(sys.argv) < 2:
    print("usage: %s host:job:scene")
    sys.exit(1)

conn = flapi.Connection("localhost")
try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

# Open the scene
scene_path = conn.Scene.parse_path( sys.argv[1] )

try:
    scene = conn.Scene.open_scene( scene_path )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Create RenderSetup
print( "Create RenderSetup for Scene")
renderSetup = conn.RenderSetup.create_from_scene( scene )

# Check that at least one deliverable is enabled
if 0 not in [renderSetup.get_deliverable(i).Disabled for i in range(renderSetup.get_num_deliverables())]:
    print("No render deliverables are enabled in this scene. Enable at least one in the Render View in the Baselight UI and save the scene.")
    sys.exit(1)

# Create Queue Manager
print( "Opening QueueManager connection" )
qm = conn.QueueManager.create_local()

# Submit render job to Queue
print( "Submitting to queue" )
opinfo = renderSetup.submit_to_queue( qm, "FLAPI Render Test " + sys.argv[1] )

print( "Created operation id %d" % opinfo.ID )
if opinfo.Warning != None:
    print( "Warning: %s" % opinfo.Warning )

# We're finished with RenderSetup now
renderSetup.release()

# We're finished with Scene now
scene.close_scene()
scene.release()

# Wait on job to finish
print( "Waiting on render job to complete" )
while True:
    opstat = qm.get_operation_status( opinfo.ID )
    print( "  Status: {Status} {Progress:.0%} {ProgressText}".format(**vars(opstat)) )
    if opstat.Status == "Done":
        break
    time.sleep(0.5)

print( "Operation complete" )

# Remove completed operation from queue
print( "Archiving operaton" )
qm.archive_operation( opinfo.ID )

qm.release()

