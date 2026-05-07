import flapi
import sys

conn = flapi.Connection("localhost")

try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

templateStr = sys.argv[1]
newSceneStr = sys.argv[2]

templatePath = conn.Scene.parse_path( templateStr )
newScenePath = conn.Scene.parse_path( newSceneStr )

options = {
    "template":templatePath
}

try:
    newScene = conn.Scene.new_scene( newScenePath, options )
except flapi.FLAPIException as ex:
    print( "Error creating new scene: %s" % ex )
    sys.exit(1)

newScene.save_scene()
newScene.close_scene()
newScene.release()

conn.close()
