# Displays a MessageDialog whenever a scene is opened

import flapi

conn = flapi.Connection.get()
app = conn.Application.get()

# Define a funcion to handle 'SceneOpen' signal
def onSceneOpen( sender, signal, args ):
    curSceneName = app.get_current_scene_name()
    allSceneNames = app.get_open_scene_names()
    # Display a message dialog containing scene info
    app.message_dialog(
        "Open Scenes",
        "You just opened the scene '%s'.\n\nThere are %i scenes open, including galleries:\n\n%s."\
            % (curSceneName, len(allSceneNames), ", ".join(allSceneNames).rstrip(", ")),
            ["OK"])

# Subscribe to 'SceneOpen' signal
app.connect( "SceneOpened", onSceneOpen )
