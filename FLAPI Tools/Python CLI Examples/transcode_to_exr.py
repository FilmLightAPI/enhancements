import flapi
import sys
import time

if len(sys.argv) < 2:
    print("usage: %s <path-to-source-movie> <dest-folder>")
    sys.exit(1)

conn = flapi.Connection()
try:
    conn.launch()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

# Open the source movie
moviePath = sys.argv[1]
try:
    seqDesc = conn.SequenceDescriptor.get_for_file( moviePath )
except flapi.FLAPIException as ex:
    print( f"Cannot read movie {moviePath}: {ex}" )
    sys.exit(1) 

# Create a temporary scene
sceneOptions = flapi.NewSceneOptions(
    format="HD 1920x1080",
    colourspace="FilmLight_TLog_EGamut",
    frame_rate=2.0
)

try:
    scene = conn.Scene.temporary_scene( sceneOptions )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Insert the sequence
scene.start_delta("Insert Sequence")
scene.insert_sequence(seqDesc, flapi.INSERT_START )
scene.end_delta()

# Create RenderSetup
print( "Create RenderSetup for Scene")
renderSetup = conn.RenderSetup.create_from_scene( scene )

# Add a RenderDeliverable to render to EXR
renderSetup.delete_all_deliverables()

deliverable = flapi.RenderDeliverable()
deliverable.Name = "EXR"
deliverable.Disabled = 0
deliverable.IsMovie = 0
deliverable.FileType = "EXR"
deliverable.OutputDirectory = sys.argv[2]
deliverable.FileNamePrefix = "render_"
deliverable.FileNamePostfix = ""
deliverable.FileNameExtension = ".exr"
deliverable.FileNameNumDigits = 7
deliverable.FileNameNumber = flapi.RENDER_FRAMENUM_SHOT_FRAME
deliverable.RenderFormat = "HD 1920x1080"
deliverable.RenderColourSpace = "ACES_lin"
renderSetup.add_deliverable( deliverable )

# Render the RenderSetup with RenderProcessor
rp = conn.RenderProcessor.get()

rp.start( renderSetup )

while True:
    progress = rp.get_progress()
    print(progress)

    if progress.Status == flapi.OPSTATUS_DONE:
        break

    time.sleep(1)


rp.shutdown()
