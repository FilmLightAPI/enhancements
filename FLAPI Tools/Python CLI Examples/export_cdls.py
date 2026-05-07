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

# ------------ export single CDL per shot ------------

exSettings = flapi.CDLExportSettings()
exSettings.Directory = sys.argv[2]

exSettings.Format = flapi.CDLEXPORT_FORMAT_CC

print( "Submitting CDL export to queue" )
exportInfo = ex.do_export_CDL( qm, scene, exSettings)
waitForExportToComplete(qm, exportInfo)

qm.release()

