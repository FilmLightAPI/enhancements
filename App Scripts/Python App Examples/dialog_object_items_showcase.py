# Creates a dialog that allows user to individually view all supported DialogItem types

import flapi
import os

#
# Define a dialog class which uses DynamicDialog to present a dialog to the user.
# 

class MyDialog:
    def __init__(self, conn):
        self.conn = conn
        # self.app = self.conn.Application.get()
        # self.scene = self.app.get_current_scene()

        # Define options for the main dropdown matching all supported possible DialogItems
        self.options = [
            {"Key": "DIT_STRING", "Text": "String"},
            {"Key": "DIT_INTEGER", "Text": "Integer"},
            {"Key": "DIT_FLOAT", "Text": "Floating-point number"},
            {"Key": "DIT_TIMECODE", "Text": "Timecode"},
            {"Key": "DIT_DROPDOWN", "Text": "Dropdown"},
            {"Key": "DIT_FILEPATH", "Text": "File Path"},
            {"Key": "DIT_IMAGEPATH", "Text": "Image Path"},
            {"Key": "DIT_DIRECTORY", "Text": "Directory Path"},
            {"Key": "DIT_STATIC_TEXT", "Text": "Static Text"},
            {"Key": "DIT_SHOT_SELECTION", "Text": "Shot Selection"},
            {"Key": "DIT_SHOT_CATEGORY", "Text": "Shot Category"},
            {"Key": "DIT_SHOT_CATEGORY_SET", "Text": "Shot Category Set"},
            {"Key": "DIT_MARK_CATEGORY", "Text": "Mark Category"},
            {"Key": "DIT_MARK_CATEGORY_SET", "Text": "Mark Category Set"}
        ]

        # Define items to show in dialog -- all supported DialogItems in this case
        self.items = [
            #Required arguments will vary depending on type
            flapi.DialogItem(
                Key="DialogItemChooser",
                Label="Choose DialogItem type",
                Type=flapi.DIT_DROPDOWN,
                Options = self.options,
                Default = "DIT_STRING"
                ),
            flapi.DialogItem(
                Key=self.options[0]['Key'],
                Label=self.options[0]['Text'],
                Type=flapi.DIT_STRING,
                Default = "default string"
                ),
            flapi.DialogItem(
                Key=self.options[1]['Key'],
                Label=self.options[1]['Text'],
                Type=flapi.DIT_INTEGER,
                IntMin=0, IntMax=100, Default = 50
                ),
            flapi.DialogItem(
                Key=self.options[2]['Key'],
                Label=self.options[2]['Text'],
                Type=flapi.DIT_FLOAT,
                FloatMin=0, FloatMax=100, FloatSnap = 0.1,
                Default = 50
                ),
            flapi.DialogItem(
                Key=self.options[3]['Key'],
                Label=self.options[3]['Text'],
                Type=flapi.DIT_TIMECODE,
                Default = [1, 1, 1, 1] # Hours, mins, seconds, frames
                ), 
            flapi.DialogItem(
                Key=self.options[4]['Key'],
                Label=self.options[4]['Text'],
                Type=flapi.DIT_DROPDOWN,\
                Options = [{"Key": x, "Text": x} for x in\
                    ["hearts", "stars", "horseshoes", "clovers", "blue moons", "unicorns", "rainbows", "red balloons"]],
                Default = "hearts"),
            flapi.DialogItem(
                Key=self.options[5]['Key'],
                Label=self.options[5]['Text'],
                Type=flapi.DIT_FILEPATH,
                Default=os.getenv("HOME")
                ),
            flapi.DialogItem(
                Key=self.options[6]['Key'],
                Label=self.options[6]['Text'],
                Type=flapi.DIT_IMAGEPATH,
                Default=os.getenv("HOME")
                ),
            flapi.DialogItem(
                Key=self.options[7]['Key'],
                Label=self.options[7]['Text'],
                Type=flapi.DIT_DIRECTORY,
                Default=os.getenv("HOME")
                ),
            flapi.DialogItem(
                Key=self.options[8]['Key'],
                Label=self.options[8]['Text'],
                Type=flapi.DIT_STATIC_TEXT,
                Default = "Useful for error messages."
                ),
            flapi.DialogItem(
                Key=self.options[9]['Key'],
                Label=self.options[9]['Text'],
                Type=flapi.DIT_SHOT_SELECTION
                ),
            flapi.DialogItem(
                Key=self.options[10]['Key'],
                Label=self.options[10]['Text'],
                Type=flapi.DIT_SHOT_CATEGORY
                ),
            flapi.DialogItem(
                Key=self.options[11]['Key'],
                Label=self.options[11]['Text'],
                Type=flapi.DIT_SHOT_CATEGORY_SET
                ),
            flapi.DialogItem(
                Key=self.options[12]['Key'],
                Label=self.options[12]['Text'],
                Type=flapi.DIT_MARK_CATEGORY
                ),
            flapi.DialogItem(
                Key=self.options[13]['Key'],
                Label=self.options[13]['Text'],
                Type=flapi.DIT_MARK_CATEGORY_SET
                )
        ]

        # Create an empty dictionary for the default settings for the dialog
        self.settings = {
        }

        # Create dialog, which will be shown later
        self.dialog = self.conn.DynamicDialog.create( 
            "DialogItems Showcase",
            self.items,
            self.settings
        )

        # Wire up the 'SettingsChanged' signal so the dialog can respond to input
        self.dialog.connect("SettingsChanged", self.onSettingsChanged)

    def onSettingsChanged(self, sender, signal, args):
        # Handle changes to the dialog

        valid = 1
        newArgs = args

        # Create a set defining which DialogItems are hidden -- hide all but the DialogItem chooser dropdown to start
        self.exclude = set([x['Key'] for x in self.options])

        # Now unhide the chosen DialogItem
        self.exclude.remove(newArgs['DialogItemChooser'])

        return { 
            "Valid"     : valid, 
            "Settings"  : newArgs,
            "Exclude"   : self.exclude
            }

    def show(self):
        # Show the dialog modally
        #
        # If the user clicks OK, the settings from the dialog will be returned
        # as a dictionary
        #
        # If the user clicks Cancel, None will be returned.
        # 
        # If you pass a negative width/height, it will add this width/height to the
        # default with of the contents of the dialog.
        #
        return self.dialog.show_modal(-200, -50)

#
# Define a MenuItem class which will be used to launch our dialog when it is selected.
#

class MyDialogMenuItem:
    def __init__(self, conn):
        self.conn = conn
        
        # Create the menu item
        # Listen to its MenuItemSelected signal to launch the dialog
        self.menuItem = conn.MenuItem.create( "Show DialogItems Showcase" )
        self.menuItem.register( flapi.MENULOCATION_SCENE_MENU )
        self.menuItem.connect( "MenuItemSelected", self.handle_menu_item )

        # Listen to its MenuItemUpdate signal to set state on the MenuItem (disabled if no scene is open)
        self.menuItem.connect( "MenuItemUpdate", self.handle_menu_item_state )
        
        # create the dialog, which we will use later.
        self.dialog = MyDialog( self.conn )

    def handle_menu_item( self, sender, signal, args ):
        result = self.dialog.show()
        if result:
            # Need to fetch an instance of the Application class to
            # use the message_dialog method.

            # The dialog message is the key of the chosen DialogItem and its value
            self.app.message_dialog( 
                "Dialog Results",
                "%s: %s" % (result['DialogItemChooser'], result[result['DialogItemChooser']]),
                ["OK"]
            )

    def handle_menu_item_state(self, sender, signal, arags):
        # Check to see if we have an open scene (required for some of the DialogItems to work)
        self.app = self.conn.Application.get()
        scene = self.app.get_current_scene()
        self.menuItem.set_enabled(scene != None)

#
# Connect to FLAPI and create the menu item
#

conn = flapi.Connection.get()
menuItem = MyDialogMenuItem( conn )