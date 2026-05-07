# Makes a ListDialog, triggerable by a MenuItem, which is enabled only if a scene is open

import flapi

scene = None

# Define a function to return input colour spaces for all shots
def get_all_shot_input_colourspaces():
    shot_input_colourspaces = []

    # Lookup shots
    nshots = scene.get_num_shots()

    if nshots > 0:
        shots = scene.get_shot_ids(0, nshots)

        # Get Shot IDs
        for shot_ix, shot_inf in enumerate(shots):

            # Get shot object
            shot = scene.get_shot(shot_inf.ShotId)

            if shot is not None:
                # Wrap with Try as some geneator-type sequences may not have an input colour space
                try:                
                    # Format as ListDialog likes: a list of key/value pairs
                    shot_input_colourspaces.append({"Key": shot_ix, "Text": "Shot %i: %s" % (shot_ix, shot.get_actual_input_colour_space())})
                    shot.release()
                except Exception as e:
                    print(e, flush=True)
    
    return shot_input_colourspaces

# Define handler function for "MenuItemSelected" signal of 'list_dialog_menu_item'
def onListDialogMenuItemSelected(sender, signal, args):
    # Get all shot input colour spaces
    shot_input_colour_spaces = get_all_shot_input_colourspaces()
    # Create the list dialog, providing title, button text and items
    result = app.list_dialog("Shot Input Colourspaces", "Choose", shot_input_colour_spaces)
    # Find the dict with the key matching the result
    choice = [x for x in shot_input_colour_spaces if x['Key'] == result][0]
    # Write the user's choice to the application log
    app.log("Example Log Category", flapi.LOGSEVERITY_SOFT, "User chose '%s'." % choice['Text'])
    # And also display the result in a MessageDialog
    app.message_dialog( 
                "Dialog Done",
                "User chose '%s'." % choice['Text'],
                ["OK"]
            )

# Define handler function for "MenuItemUpdate" signal of 'list_dialog_menu_item'
# (This signal fires just before menu item is displayed)
def onListDialogMenuItemUpdate(sender, signal, args):
    global scene
    # Enable menu item only if a scene is open
    scene = app.get_current_scene()
    list_dialog_menu_item.set_enabled(scene != None)

# Connect to FLAPI
conn = flapi.Connection.get() 
conn.connect()

# Get application
app = conn.Application.get()
 
# Place menu item on Scene menu
list_dialog_menu_item = conn.MenuItem.create("Show List Dialog")
list_dialog_menu_item.register(flapi.MENULOCATION_SCENE_MENU)

# Connect up both the 'MenuItemSelected' and 'MenuItemUpdate' signals
list_dialog_menu_item.connect("MenuItemSelected", onListDialogMenuItemSelected)
list_dialog_menu_item.connect("MenuItemUpdate", onListDialogMenuItemUpdate)