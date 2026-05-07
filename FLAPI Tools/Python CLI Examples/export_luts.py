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

# ------------ first example - export single LUT per shot ------------

exSettings = flapi.CubeExportSettings()
exSettings.Directory = sys.argv[2]

exSettings.LUTFormat = flapi.CUBEEXPORT_LUTFORMAT_TRUELIGHT

exSettings.NumLUTs= 1
exSettings.LUT1Options = {  flapi.CUBEEXPORT_LUT3OPTIONS_INPUT, flapi.CUBEEXPORT_LUT3OPTIONS_GRADE, flapi.CUBEEXPORT_LUT3OPTIONS_OUTPUT  } 
exSettings.LUT1Name = "%{Clip}_all"

print( "Submitting LUT export to queue" )
exportInfo = ex.do_export_cube( qm, scene, exSettings)
waitForExportToComplete(qm, exportInfo)


# -------------- second example - export multiple luts ----------------

exSettings.InputColourSpace = "sRGB"
exSettings.OutputColourSpace = "FilmLight_Linear_EGamut"

exSettings.NumLUTs= 3

exSettings.LUT1Options = {  flapi.CUBEEXPORT_LUT3OPTIONS_INPUT  } 
exSettings.LUT1Name = "%{Clip}_input"

exSettings.LUT2Options = {  flapi.CUBEEXPORT_LUT3OPTIONS_GRADE  } 
exSettings.LUT2Name = "%{Clip}_grade"

exSettings.LUT3Options = {  flapi.CUBEEXPORT_LUT3OPTIONS_OUTPUT  } 
exSettings.LUT3Name = "%{Clip}_to_output"

print( "Submitting LUT export to queue" )
exportInfo = ex.do_export_cube( qm, scene, exSettings)
waitForExportToComplete(qm, exportInfo)

qm.release()

