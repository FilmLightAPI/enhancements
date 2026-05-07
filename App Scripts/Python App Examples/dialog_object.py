# Makes a simple DynamicDialog tied to a MenuItem

import flapi
import time

#
# Define a dialog class which uses DynamicDialog to present a dialog to the user
# 

class MyDialog:
    def __init__(self, conn):
        self.conn = conn

        # Define items to show in dialog
        self.items = [
            flapi.DialogItem(Key="Name", Label="Name", Type=flapi.DIT_STRING, Default = ""),
            flapi.DialogItem(Key="Desc", Label="Description", Type=flapi.DIT_STRING, Default = ""),
        ]

        # Create an empty dictionary for the default settings for the dialog
        self.settings = {
            "Name": "",
            "Desc": "",
        }

        # Create dialog, which will be shown later
        self.dialog = self.conn.DynamicDialog.create( 
            "My Dialog",
            self.items,
            self.settings
        )

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
        self.menuItem = conn.MenuItem.create( "Show My Dialog" )
        self.menuItem.register( flapi.MENULOCATION_APP_MENU )
        self.menuItem.connect( "MenuItemSelected", self.handle_menu_item )
        
        # Create the dialog, which we will use later
        self.dialog = MyDialog( self.conn )

    def handle_menu_item( self, sender, signal, args ):
        result = self.dialog.show()
        if result:
            # Show results
            #
            # Need to fetch an instance of the Application class to
            # use the message_dialog method
            #
            app = self.conn.Application.get()
            app.message_dialog( 
                "Dialog Done",
                "Name was '%s' and Description was '%s'." % (result['Name'], result['Desc']),
                ["OK"]
            )


#
# Connect to FLAPI and create the menu item
#

conn = flapi.Connection.get()
menuItem = MyDialogMenuItem( conn )
