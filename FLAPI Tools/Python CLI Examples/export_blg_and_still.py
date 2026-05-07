from __future__ import print_function
import flapi
import sys
import time

def waitForExportToComplete( qm, exportInfo ):
    for msg in exportInfo.Log:
        if (msg.startswith("Error")):
            print("Export Submission Failed.  %s" % msg);
            return

    print( "Waiting on render job to complete" )
    triesSinceChange = 0
    lastProgress = -1
    maxTries = 20
    while True:
        opstat = qm.get_operation_status( exportInfo.ID )
        triesSinceChange +=1 
        if opstat.Progress != lastProgress:
            triesSinceChange = 0
            lastProgress = opstat.Progress
        dots = ""
        if (triesSinceChange > 0):
            dots = "..."[:(triesSinceChange%3)+1]
        else:
            print("")
        print( "\r  Status: {Status} {Progress:.0%} {ProgressText} ".format(**vars(opstat)), end=""), 
        print("%s    " % dots, end=""),
        sys.stdout.flush()
        if opstat.Status == "Done":
            print( "\nExport complete" )
            break
        if triesSinceChange == maxTries:
            print("\nStopped waiting for queue to complete.")
            break
        time.sleep(0.5)

    exportLog = qm.get_operation_log( exportInfo.ID )
    for l in exportLog:
        print( "   %s %s: %s" % (l.Time, l.Message, l.Detail) )

if len(sys.argv) < 3:
    print("usage: %s host:job:scene output_directory" % sys.argv[0])
    sys.exit(1)

conn = flapi.Connection("localhost")
conn.connect()

# Open the scene
scene_path = conn.Scene.parse_path( sys.argv[1] )

try:
    scene = conn.Scene.open_scene( scene_path, {  flapi.OPENFLAG_DISCARD  } )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Create Queue Manager
print( "Opening QueueManager connection" )
qm = conn.QueueManager.create_local()

ex = conn.Export.create()

# Simple BLG Export example

exSettings = flapi.BLGExportSettings()

exSettings.Directory = sys.argv[2]
exSettings.Scale = 4
exSettings.Template = "%{Job}/%{Clip}_%{TimelineFrame}"
exSettings.ViewingColourSpace = "Video_Full"
exSettings.ViewingFormat = "HD 1280x720"
exSettings.Overwrite = flapi.EXPORT_OVERWRITE_REPLACE

# Submit render job to Queue
print( "Submitting BLG export to queue" )
exportInfo = ex.do_export_BLG( qm, scene, exSettings)
waitForExportToComplete(qm, exportInfo)

# More complicated Still Export example where we are choosing the shots we want exported.

nshots = scene.get_num_shots()

if nshots > 0:
    shots = scene.get_shot_ids(0, nshots)
    for shot_ix, shot_inf in enumerate(shots):
        if (shot_ix % 2):
            print("Adding Shot %d (%d) to export" % (shot_ix, shot_inf.ShotId))
        
            # Get Shot object for shot with the given ID
            shot = scene.get_shot(shot_inf.ShotId)
            ex.select_shot(shot);
        
            # Release Shot object - commented out for now - it seems bad things happen if you release this too early.
            # shot.release()

exSettings = flapi.StillExportSettings()
exSettings.ColourSpace = "sRGB"
exSettings.Format = "HD 1920x1080"
exSettings.Overwrite = flapi.EXPORT_OVERWRITE_REPLACE
exSettings.Directory = sys.argv[2]
exSettings.Frames = flapi.EXPORT_FRAMES_FIRST 
exSettings.Filename = "%{Job}/%{Clip}_%{TimelineFrame}"
exSettings.Source = flapi.EXPORT_SOURCE_SELECTEDSHOTS

print( "Submitting to queue" )
exportInfo = ex.do_export_still( qm, scene, exSettings)

waitForExportToComplete(qm, exportInfo)

qm.release()

